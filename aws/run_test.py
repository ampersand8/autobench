#!/usr/bin/env python3
import subprocess
import uuid

UUID = str(uuid.uuid1())
keyPairName = 'awssetup'
publicip = open('publicIp.txt', 'r').read()
testRemoteCmd = "./run_test.sh"
testType = "replicaset"
executeTestCmd = ["ssh", "-i", keyPairName + ".key", "ubuntu@" + publicip, testRemoteCmd]
subprocess.call(executeTestCmd,timeout=10800)
downloadCommand = ["scp", "-r", "-o", "StrictHostKeyChecking=no", "-i", keyPairName + ".key", "ubuntu@" + publicip + ":./results", "results/test." + testType + "." +  UUID]
subprocess.call(downloadCommand)