#!/bin/bash
# Continously runs complete test cycles
# With Parameter startOffset, an offset for the testnames can be given
startOffset=${1}
counter=0
logfile=continuous.log
while true
do
    counter=$((counter + 1))
    echo "Starting Test ${counter} at $(date)" >> ${logfile}
	testName="aws$(printf %02d $((counter + startOffset)))"
    ./setup_aws.py -e -c -n ${testName}
    sleep 120
    ./cleanup_aws.py
    sleep 120
    echo "Test ${counter} ended at $(date)" >> ${logfile}
done
