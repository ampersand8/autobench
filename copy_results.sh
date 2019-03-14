#!/bin/bash
# Example: ./copyResults /home/user/gowork/src/github.com/ampersand8/autobench/aws/results /home/user/bachelorthesis/listings 01 20
# Example above copies all test runs 01 to 20
sourceDir=${1}
targetDir=${2}
startRange=${3}
endRange=${4}
for ((i=${startRange}; i<=${endRange}; i++)); do
	run="$(printf %02d ${i})"
	nats_dest="${targetDir}/nats_tests/aws${run}"
	kafka_dest="${targetDir}/kafka_tests/aws${run}"
	result_src="${sourceDir}/aws${run}"
	cp -a ${result_src}/nats_* ${nats_dest}
	cp -a ${result_src}/kafka_* ${kafka_dest}
	cp -a ${nats_dest}/T01* ${targetDir}/nats_tests/awsT01/${run}.txt
	cp -a ${nats_dest}/T02* ${targetDir}/nats_tests/awsT02/${run}.txt
	cp -a ${nats_dest}/T03* ${targetDir}/nats_tests/awsT03/${run}.txt
	cp -a ${nats_dest}/T04* ${targetDir}/nats_tests/awsT04/${run}.txt
	cp -a ${kafka_dest}/T01* ${targetDir}/kafka_tests/awsT01/${run}.txt
	cp -a ${kafka_dest}/T02* ${targetDir}/kafka_tests/awsT02/${run}.txt
	cp -a ${kafka_dest}/T03* ${targetDir}/kafka_tests/awsT03/${run}.txt
	cp -a ${kafka_dest}/T04* ${targetDir}/kafka_tests/awsT04/${run}.txt
done
