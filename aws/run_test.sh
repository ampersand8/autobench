#!/bin/bash
set -e
source helper.sh

echo "Running Test"
ansible-playbook --private-key=awssetup.key run_test_playbook.yml

echo "Fetching results"
mkdir results
scp -r -o StrictHostKeyChecking=no -i awssetup.key test:./test/T0* results/
echo "Done"