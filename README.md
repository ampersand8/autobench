# Examples
```
./autobench -h
```

# Manual Test
## Example using autobench
Following example tests Apache Kafka and NATS directly with autobench. The first test defines all possible arguments while the second test uses the defaults.
```
./autobench -cluster kafka -url "kafka-node-0.service.consul:9092,kafka-node-1.service.consul:9092,kafka-node-2.service.consul:9092" -rate 100000 -connections 2 -duration 10m -payload 128 -out kafka_results.txt```
./autobench -url nats://user:password@nats-service.service.consul:4222
```

# Automated Test
## Requirements
For automated tests access to AWS is necessary. Create an API Key on AWS and save it in `~/.aws/credentials`. The config should look as following:
`~/.aws/config`:
```
[default]
region = eu-west-1
```

`~/.aws/credentials`:
```
[default]
aws_access_key_id = MYAWSKEY
aws_secret_access_key = MYAWSSECRET
```

## Run Tests
Following example shows the commands necessary to run the tests and analyse the results. As an output there will be graphs for the pings and latency measurements.
```
cd aws/
# Runs the tests in an infite loop, until it's interrupted with Ctrl^C
./continuous_testing.sh
Ctrl^C
cd ..
# Copy the results
./copyResults.sh /home/user/gowork/src/github.com/ampersand8/autobench/aws/results /home/user/bachelorthesis/listings 01 20
cd /home/user/bachelorthesis/listings

# Process all the environment measurements
/home/user/gowork/src/github.com/ampersand8/autobench/process_env_result_files.py --testruns 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20

# Calc the standard deviations for pings in different testcases and generate graph with errorbars
/home/user/gowork/src/github.com/ampersand8/autobench/calc_ping_standard_deviations.py --testcase T01
/home/user/gowork/src/github.com/ampersand8/autobench/calc_ping_standard_deviations.py --testcase T02
/home/user/gowork/src/github.com/ampersand8/autobench/calc_ping_standard_deviations.py --testcase T03
/home/user/gowork/src/github.com/ampersand8/autobench/calc_ping_standard_deviations.py --testcase T04

# Calc the standard deviations for latency measurements in different testcases and generate graph with errorbars
/home/user/gowork/src/github.com/ampersand8/autobench/calc_standard_deviations.py --testcase T01 --testruns 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
/home/user/gowork/src/github.com/ampersand8/autobench/calc_standard_deviations.py --testcase T02 --testruns 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
/home/user/gowork/src/github.com/ampersand8/autobench/calc_standard_deviations.py --testcase T03 --testruns 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
/home/user/gowork/src/github.com/ampersand8/autobench/calc_standard_deviations.py --testcase T04 --testruns 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
```