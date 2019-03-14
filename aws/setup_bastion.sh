#!/bin/bash
set -e
source helper.sh

KAFKA_PLAYBOOK="setup_kafka_playbook.yml"
NATS_PLAYBOOK="setup_nats_playbook.yml"
KAFKA_TEST_PLAYBOOK="setup_kafka_test_playbook.yml -e connection_string=kafka0:9092 -e cluster=kafka"
NATS_TEST_PLAYBOOK="setup_nats_test_playbook.yml -e connection_string=nats://nats0:4222 -e cluster=nats"

## Download necessary packages
echo "Installing necessary packages on bastion"
sudo apt-get -qq update && sudo apt-get -qq install curl tmux python ansible -y > /dev/null 2>&1 &
BASTION_INSTALL_PID=$!

cat <<EOF | tee /home/ubuntu/.ssh/config > /dev/null
IdentityFile /home/ubuntu/awssetup.key
EOF

cat <<EOF | sudo tee -a /etc/hosts > /dev/null
192.168.1.10    kafka0
192.168.1.20    nats0
192.168.2.20    bastion0
192.168.1.100   test0
192.168.1.101   test1
EOF

sleep 10

echo "Start Test Ansible preparation"
TEST_INSTALL_PIDS=()
ssh -q -o StrictHostKeyChecking=no -i awssetup.key test0 "sudo apt-get -qq update && sudo apt-get -qq install python > /dev/null 2>&1" &
ssh -q -o StrictHostKeyChecking=no -i awssetup.key test1 "sudo apt-get -qq update && sudo apt-get -qq install python > /dev/null 2>&1" &
TEST_INSTALL_PIDS+=($!)

echo "Start Kafka Ansible preparation"
MSG_INSTALL_PIDS=()
ssh -q -o StrictHostKeyChecking=no -i awssetup.key kafka0 "sudo apt-get -qq update && sudo apt-get -qq install python -y > /dev/null 2>&1" &
MSG_INSTALL_PIDS+=($!)
ssh -q -o StrictHostKeyChecking=no -i awssetup.key nats0 "sudo apt-get -qq update && sudo apt-get -qq install python -y > /dev/null 2>&1" &
MSG_INSTALL_PIDS+=($!)

echo "Waiting for Bastion Install to finish"
wait_for_pids "${BASTION_INSTALL_PID}"
cat <<EOF | sudo tee -a /etc/ansible/hosts > /dev/null
[test]
test0
test1
[kafkaTest]
test0
[natsTest]
test1
[kafka]
kafka0
[nats]
nats0
EOF

echo "Waiting for Kafka Ansible preparation to finish"
(wait_for_pids "${MSG_INSTALL_PIDS[@]}" && ansible-playbook --private-key=awssetup.key -f 25 ${KAFKA_PLAYBOOK}) &
(wait_for_pids "${MSG_INSTALL_PIDS[@]}" && ansible-playbook --private-key=awssetup.key -f 25 ${NATS_PLAYBOOK}) &

echo "Waiting for Test Ansible preparation to finish"
(wait_for_pids "${TEST_INSTALL_PIDS[@]}" && ansible-playbook --private-key=awssetup.key -f 25 ${KAFKA_TEST_PLAYBOOK}) &
(wait_for_pids "${TEST_INSTALL_PIDS[@]}" && ansible-playbook --private-key=awssetup.key -f 25 ${NATS_TEST_PLAYBOOK}) &

echo "Waiting for all setups to finish"
wait
scp -o StrictHostKeyChecking=no -i awssetup.key environment_tests.sh test0:./
scp -o StrictHostKeyChecking=no -i awssetup.key environment_tests.sh test1:./
scp -o StrictHostKeyChecking=no -i awssetup.key environment_tests.sh kafka0:./
scp -o StrictHostKeyChecking=no -i awssetup.key environment_tests.sh nats0:./

echo "Running Test"
ansible-playbook --private-key=awssetup.key run_test_playbook.yml

echo "Fetching results"
uuid=$(uuidgen)
mkdir -p results/kafka_${uuid}/env
mkdir -p results/nats_${uuid}/env
scp -r -o StrictHostKeyChecking=no -i awssetup.key test0:./test/T0* results/kafka_${uuid}/
scp -r -o StrictHostKeyChecking=no -i awssetup.key test1:./test/T0* results/nats_${uuid}/

scp -r -o StrictHostKeyChecking=no -i awssetup.key test0:./env_* results/kafka_${uuid}/env/
scp -r -o StrictHostKeyChecking=no -i awssetup.key kafka0:./env_* results/kafka_${uuid}/env/
scp -r -o StrictHostKeyChecking=no -i awssetup.key test1:./env_* results/nats_${uuid}/env/

echo "Done"