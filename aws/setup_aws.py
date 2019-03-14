#!/usr/bin/env python3

import boto3
import argparse
import uuid
import os
from time import sleep
import subprocess
import paramiko
import socket

ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

UUID = str(uuid.uuid1())

parser = argparse.ArgumentParser(description='Setup a VPC with Workload Instances and a Bastion Host on AWS')
parser.add_argument('--kafka-instance-type', nargs='?', dest='kafkaInstanceType',
                   default='m4.xlarge',
                   help='instance type for kafka instances (default: m4.xlarge)')
parser.add_argument('--kafka-volume-type', nargs='?', dest='kafkaVolumeType',
                   default='io1',
                   help='volume type for kafka volumes (default: io1)')
parser.add_argument('--kafka-volume-size', nargs='?', type=int, dest='kafkaVolumeSize',
                   default=80,
                   help='volume size for kafka volumes in GB (default: 80)')
parser.add_argument('-ki', '--kafka-instances', nargs='?', type=int, dest='kafkaInstances',
                   default=1, help='number of kafka instances (default: 1)')
parser.add_argument('--nats-instance-type', nargs='?', dest='natsInstanceType',
                   default='m4.xlarge',
                   help='instance type for nats instances (default: m4.xlarge)')
parser.add_argument('--nats-volume-type', nargs='?', dest='natsVolumeType',
                   default='io1',
                   help='volume type for nats volumes (default: io1)')
parser.add_argument('--nats-volume-size', nargs='?', type=int, dest='natsVolumeSize',
                   default=10,
                   help='volume size for nats volumes in GB (default: 10)')
parser.add_argument('-ni', '--nats-instances', nargs='?', type=int, dest='natsInstances',
                   default=1, help='number of nats instances (default: 1)')
parser.add_argument('--test-instance-type', nargs='?', dest='testInstanceType',
                   default='m4.xlarge',
                   help='instance type for test instance (default: m4.xlarge)')
parser.add_argument('--test-instances', nargs='?', type=int, dest='testInstances',
                   default=2,
                   help='number of test instances (default: 2)')
parser.add_argument('-t', '--test', action='store_true', dest='executeTest',
                   help='executes the test and stores results in ../results/<testtype> (e.g. ../results/3.ycsb.t2.micro.sharding.5.ccfaa2e9-e913-4607-a578-c5eaae40724a')
parser.add_argument('-c', '--cleanup', action='store_true', dest='cleanup',
                   help='cleanup AWS after setup and/or testing')
parser.add_argument('-n', '--test-name', nargs='?', type=str, dest='testName',
                   help='name of the test (default: random UUID)')

args = parser.parse_args()

natsVolumeSizeInGB = args.natsVolumeSize
natsVolumeType = args.natsVolumeType
natsInstanceType = args.natsInstanceType
natsInstances = args.natsInstances

kafkaVolumeSizeInGB = args.kafkaVolumeSize
kafkaVolumeType = args.kafkaVolumeType
kafkaInstanceType = args.kafkaInstanceType
kafkaInstances = args.kafkaInstances

testInstanceType = args.testInstanceType
testInstances = args.testInstances
executeTest = args.executeTest
cleanup = args.cleanup
testName = args.testName if args.testName else UUID
keyPairName = 'awssetup'
filesToTransfer = [keyPairName+".key", "setup_test.sh", "setup_bastion.sh", "setup_kafka.sh", "setup_nats.sh", "setup_nats_test_playbook.yml", "setup_kafka_test_playbook.yml", "setup_kafka_playbook.yml", "setup_nats_playbook.yml", "run_test_playbook.yml", "autotest.py", "helper.sh", "run_test.sh", "environment_tests.sh"]

def check_ssh(ip, user, key, interval=10, retries=10):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for x in range(retries):
        try:
            print("SSH Connect Check " + str(x))
            ssh.connect(ip, username=user, key_filename=key)
            return True
        except (paramiko.AuthenticationException, paramiko.SSHException, socket.error) as e:
            print(e)
            sleep(interval)
    return False

print("Create Key Pair " + keyPairName)
response = client.create_key_pair(KeyName=keyPairName)
f = open(keyPairName + '.key', 'w')
f.write(response['KeyMaterial'])
f.close()
os.chmod(keyPairName + ".key", 0o600)

instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
for instance in instances:
    print(instance.id, instance.instance_type)

for status in ec2.meta.client.describe_instance_status()['InstanceStatuses']:
    print(status)

print("Create VPC")
vpc = ec2.create_vpc(CidrBlock='192.168.0.0/16', InstanceTenancy='dedicated')
sleep(2)
vpc.create_tags(Tags=[{"Key": "Name", "Value": "awssetup"}])
vpc.wait_until_available()
print(vpc.id)

print("Create Internet Gateway")
ig = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=ig.id)
print(ig.id)

print("Create Private Subnet")
private_subnet = ec2.create_subnet(CidrBlock='192.168.1.0/24', VpcId=vpc.id)
sleep(2)
subnet_waiter = client.get_waiter('subnet_available')
subnet_waiter.wait(SubnetIds=[private_subnet.id])
client.create_tags(Resources=[private_subnet.id],Tags=[{'Key':'Name','Value':'Private Subnet'}])
print(private_subnet.id)

print("Create Public Subnet")
public_subnet = ec2.create_subnet(CidrBlock='192.168.2.0/24', VpcId=vpc.id)
sleep(2)
subnet_waiter.wait(SubnetIds=[public_subnet.id])
client.create_tags(Resources=[public_subnet.id],Tags=[{'Key':'Name','Value':'Public Subnet'}])
print(public_subnet.id)

print("Allocating an Elastic IP")
eip = client.allocate_address(Domain='vpc')

print("Create NAT Gateway - takes a moment")
nat_gw = client.create_nat_gateway(SubnetId=public_subnet.id, AllocationId=eip['AllocationId'])
waiter = client.get_waiter('nat_gateway_available')
waiter.wait(NatGatewayIds=[nat_gw['NatGateway']['NatGatewayId']])
print(nat_gw)

print("Create Public Route Table")
public_route_table = vpc.create_route_table()
public_route = public_route_table.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=ig.id
)
print(public_route_table.id)

print("Get Private Route Table (main)")
private_route_table = client.describe_route_tables(Filters=[{'Name': 'association.main', 'Values': ["true"]}])['RouteTables'][0]
client.create_route(DestinationCidrBlock='0.0.0.0/0',
        GatewayId=nat_gw['NatGateway']['NatGatewayId'],
        RouteTableId=private_route_table['RouteTableId'])

print(private_route_table['RouteTableId'])

print("Associating Private Route Table with Public Subnet")
public_route_table.associate_with_subnet(SubnetId=public_subnet.id)

print("Create Security Group")
sec_group = ec2.create_security_group(
    GroupName='mydefault', Description='mydefault sec group', VpcId=vpc.id)
sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='tcp',
    FromPort=22,
    ToPort=40000
)
sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='icmp',
    FromPort=-1,
    ToPort=-1
)
print(sec_group.id)

print("Provision Kafka Instances")
for i in range(0,kafkaInstances):
    print("Deploying Kafka " + str(i+1) + "/" + str(kafkaInstances))
    nameTag = [{"Key": "Name", "Value": "kafka" + str(i)},{"Key": "group", "Value": "workload"}]
    hostIp = i + 10
    instances = ec2.create_instances(
        ImageId='ami-0b91bd72',
        InstanceType=kafkaInstanceType,
        MaxCount=1,
        MinCount=1,
        KeyName=keyPairName,
        NetworkInterfaces=[{
            'SubnetId': private_subnet.id,
            'DeviceIndex': 0,
            'AssociatePublicIpAddress': False,
            'PrivateIpAddress': '192.168.1.' + str(hostIp),
            'Groups': [sec_group.group_id]
        }],
        BlockDeviceMappings=[{
            'DeviceName': '/dev/sdf',
            'VirtualName': 'string',
            'Ebs': {
                'Encrypted': False,
                'DeleteOnTermination': True,
                'VolumeSize': kafkaVolumeSizeInGB,
                'VolumeType': kafkaVolumeType,
                'Iops': 50 * kafkaVolumeSizeInGB
            }
        }],
        TagSpecifications=[{'ResourceType': 'instance',
                            'Tags': nameTag}]
    )

print("Provision NATS Instances")
for i in range(0,kafkaInstances):
    print("Deploying NATS " + str(i+1) + "/" + str(natsInstances))
    nameTag = [{"Key": "Name", "Value": "nats" + str(i)},{"Key": "group", "Value": "workload"}]
    hostIp = i + 20
    instances = ec2.create_instances(
        ImageId='ami-0b91bd72',
        InstanceType=natsInstanceType,
        MaxCount=1,
        MinCount=1,
        KeyName=keyPairName,
        NetworkInterfaces=[{
            'SubnetId': private_subnet.id,
            'DeviceIndex': 0,
            'AssociatePublicIpAddress': False,
            'PrivateIpAddress': '192.168.1.' + str(hostIp),
            'Groups': [sec_group.group_id]
        }],
        TagSpecifications=[{'ResourceType': 'instance',
                            'Tags': nameTag}]
    )

print("Provision Test Instances")
for i in range(0,testInstances):
    print("Deploying Test " + str(i+1) + "/" + str(testInstances))
    nameTag = [{"Key": "Name", "Value": "test" + str(i)},{"Key": "group", "Value": "test"}]
    instances = ec2.create_instances(
        ImageId='ami-0b91bd72',
        InstanceType=testInstanceType,
        MaxCount=1,
        MinCount=1,
        KeyName=keyPairName,
        NetworkInterfaces=[{
            'SubnetId': private_subnet.id,
            'DeviceIndex': 0,
            'AssociatePublicIpAddress': False,
            'PrivateIpAddress': '192.168.1.10' + str(i),
            'Groups': [sec_group.group_id]
        }],
        TagSpecifications=[{'ResourceType': 'instance',
                            'Tags': nameTag}]
    )

public_bastion = ''
print("Deploying Bastion Host")
nameTag = [{"Key": "Name", "Value": "bastion"},{"Key": "group", "Value": "bastion"}]
bastionInstances = ec2.create_instances(
    ImageId='ami-0b91bd72',
    InstanceType='m5.large',
    MaxCount=1,
    MinCount=1,
    KeyName=keyPairName,
    NetworkInterfaces=[{
        'SubnetId': public_subnet.id,
        'DeviceIndex': 0,
        'AssociatePublicIpAddress': True,
        'PrivateIpAddress': '192.168.2.20',
        'Groups': [sec_group.group_id]
    }],
    TagSpecifications=[{'ResourceType': 'instance',
                        'Tags': nameTag}]
)
for bastionInstance in bastionInstances:
    instance_waiter = client.get_waiter('instance_running')
    instance_waiter.wait(InstanceIds=[bastionInstance.id])
    sleep(10)
    instance = client.describe_instances(InstanceIds=[bastionInstance.id])['Reservations'][0]['Instances'][0]
    print("Bastion Public IP: " + instance['PublicIpAddress'])
    f = open('publicIp.txt', 'w')
    f.write(instance['PublicIpAddress'])
    f.close()
    check_ssh(instance['PublicIpAddress'], 'ubuntu', keyPairName + ".key")
    uploadCmd = ["scp", "-o", "StrictHostKeyChecking=no", "-i", keyPairName + ".key", "ubuntu@" + instance['PublicIpAddress'] + ":./"]
    uploadCmd[5:5] = filesToTransfer
    subprocess.call(uploadCmd)
    print("ssh -i " + keyPairName + ".key ubuntu@" + instance['PublicIpAddress'])
    if executeTest:
        testRemoteCmd = "./setup_bastion.sh"
        testType = "replicaset"
        executeTestCmd = ["ssh", "-i", keyPairName + ".key", "ubuntu@" + instance['PublicIpAddress'], testRemoteCmd]
        subprocess.call(executeTestCmd,timeout=10800)
        downloadCommand = ["scp", "-r", "-o", "StrictHostKeyChecking=no", "-i", keyPairName + ".key", "ubuntu@" + instance['PublicIpAddress'] + ":./results", "results/" + testname]
        subprocess.call(downloadCommand)

    if cleanup:
            subprocess.call(["./cleanup_aws.py"])

