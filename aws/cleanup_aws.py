#!/usr/bin/env python3
import sys
import os
import boto3
from time import sleep

ec2 = boto3.resource('ec2')
client = boto3.client('ec2')
waiter_delay_in_seconds = 15
waiter_timeout_in_seconds = 300
keyPairName = 'awssetup'

instances_to_delete = []

print("Deleting Instances")
response_instances = client.describe_instances(Filters=[{'Name':'instance-state-name', 'Values':['running','stopped', 'shutting-down', 'stopping', 'pending']}])
for reservation in response_instances['Reservations']:
    for instance in reservation['Instances']:
        client.terminate_instances(InstanceIds=[instance['InstanceId']])
        instances_to_delete.append(instance['InstanceId'])

print(instances_to_delete)
if len(instances_to_delete) > 0:
    waiter = client.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=instances_to_delete)
    print("Instances successfully deleted")
else:
    print("No instances to delete")

print("Deleting Key Pair " + keyPairName)
client.delete_key_pair(KeyName=keyPairName)
if os.path.isfile(keyPairName + ".key"):
    os.remove(keyPairName + ".key")
else:    ## Show an error ##
    print("Keyfile %s does not exist" % keyPairName + ".key")

def vpc_cleanup(vpcid):
    if not vpcid:
        return
    print('Removing VPC ({}) from AWS'.format(vpcid))
    
    ec2client = ec2.meta.client
    vpc = ec2.Vpc(vpcid)

    print("Delete Security Groups")
    for sg in vpc.security_groups.all():
        if sg.group_name != 'default':
            sg.delete()
    
    filters = [
        {'Name': 'domain', 'Values': ['vpc']}
    ]

    print("Remove NAT Gateways")
    nat_gateways = client.describe_nat_gateways()
    nat_gateways_to_delete = []
    for nat_gateway in nat_gateways['NatGateways']:
        print("Deleting NAT Gateway: " + nat_gateway['NatGatewayId'])
        client.delete_nat_gateway(NatGatewayId=nat_gateway['NatGatewayId'])
        nat_gateways_to_delete.append(nat_gateway['NatGatewayId'])

    nat_gateway_deleted = False
    waited_time = 0
    while(not nat_gateway_deleted and waited_time < waiter_timeout_in_seconds):
        sleep(waiter_delay_in_seconds)
        waited_time += waiter_delay_in_seconds
        still_existing = client.describe_nat_gateways(Filters=[{'Name':'state', 'Values':['pending','available','deleting']}],NatGatewayIds=nat_gateways_to_delete)
        if (len(still_existing['NatGateways']) == 0):
            print("NAT Gateway successfully removed")
            nat_gateway_deleted = True

    print("Releasing Elatic IPs")
    eips = client.describe_addresses(Filters=filters)
    for eip in eips['Addresses']:
        print("Releasing EIP: " + eip['AllocationId'])
        client.release_address(AllocationId=eip['AllocationId'])

    print("Delete Internet Gateways")
    for gw in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=gw.id)
        gw.delete()
    
    print("Delete Route Table Associations and Custom Route Tables")
    for rt in vpc.route_tables.all():
        main = False
        for rta in rt.associations:
            if not rta.main:
                rta.delete()
            else:
                main = True
        for route in rt.routes:
            if route.destination_cidr_block != '192.168.0.0/16':
                route.delete()
        if main == False:
            rt.delete()

    print("Delete Instances")
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            instance.terminate()
    
    print("Delete Endpoints")
    for ep in ec2client.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        ec2client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])

    print("Delete VPC Peering Connections")
    for vpcpeer in ec2client.describe_vpc_peering_connections(
            Filters=[{
                'Name': 'requester-vpc-info.vpc-id',
                'Values': [vpcid]
            }])['VpcPeeringConnections']:
        ec2.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()

    print("Delete Network ACLs")
    for netacl in vpc.network_acls.all():
        if not netacl.is_default:
            netacl.delete()

    print("Delete Network Interfaces")
    for subnet in vpc.subnets.all():
        for interface in subnet.network_interfaces.all():
            interface.delete()
        subnet.delete()

    print("Detaching Network Interfaces")
    network_interfaces = client.describe_network_interfaces()
    for nic in network_interfaces['NetworkInterfaces']:
        print("Detaching Network Interface: " + nic['Attachment']['AttachmentId'])
        client.detach_network_interface(AttachmentId=nic['Attachment']['AttachmentId'])
    
    print("Delete VPC!")
    ec2client.delete_vpc(VpcId=vpcid)

for vpc in ec2.vpcs.all():
    vpc_cleanup(vpc.id)
