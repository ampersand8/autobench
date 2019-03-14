#!/bin/bash

set -e
source helper.sh

# Sets environment up for YCSB Testing
# Download YCSB, configure properties, install dependencies, prepare database
if [ -d "test" ]; then
    echo "TEST already setup! Aborting"
    exit 0
fi

connection_url=${1}
cluster=${2}

## Download necessary packages
sudo apt-get -qq update && sudo apt -qq install dnsmasq iperf curl python -y > /dev/null 2>&1 &
TEST_INSTALL_DEPENDENCY_PID=$!

cat <<EOF | sudo tee -a /etc/hosts > /dev/null
192.168.1.10    kafka0
192.168.1.20    nats0
192.168.2.20    bastion0
192.168.1.100   test0
192.168.1.101   test1
127.0.0.1       ip-192-168-1-100
127.0.0.1       ip-192-168-1-101
EOF


## Download and unpack TEST
echo "Waiting for Test Dependencies install"
wait_for_pids "${TEST_INSTALL_DEPENDENCY_PID}"

sudo echo "address=/kafka0/192.168.1.10" >> /etc/dnsmasq.conf
sudo echo "address=/nats0/192.168.1.20" >> /etc/dnsmasq.conf
sudo echo "address=/bastion0/192.168.2.20" >> /etc/dnsmasq.conf
sudo echo "address=/test0/192.168.1.100" >> /etc/dnsmasq.conf
sudo echo "address=/test1/192.168.1.101" >> /etc/dnsmasq.conf
sudo echo "address=/ip-192-168-1-10/192.168.1.10" >> /etc/dnsmasq.conf
sudo echo "address=/ip-192-168-1-20/192.168.1.20" >> /etc/dnsmasq.conf
sudo echo "address=/ip-192-168-1-100/192.168.1.100" >> /etc/dnsmasq.conf
sudo echo "address=/ip-192-168-1-101/192.168.1.101" >> /etc/dnsmasq.conf

cat <<EOF | sudo tee -a /etc/resolv.conf > /dev/null
nameserver 127.0.0.1
nameserver 8.8.8.8
search eu-west-1.compute.internal
EOF

sudo systemctl stop systemd-resolved.service
sudo systemctl restart dnsmasq.service

mkdir -p test
cd test
wget --tries=10 "https://github.com/ampersand8/autobench/master/bench.tar.gz" -O bench.tar.gz
tar xzf bench.tar.gz

cat <<EOF | sudo tee config.json > /dev/null
{
    "configuration": {
        "clusters": [
            {
                "name": "${cluster}",
                "url": "${connection_url}"
            }
        ],
        "waitBetweenTests": "30"
    },
    "tests": [
        {
            "id": "T01",
            "clusters": ["${cluster}"],
            "rate": "3000",
            "payload": "256",
            "connections": "1",
            "duration": "30m",
            "max_retries": "3"
         },
         {
            "id": "T02",
            "clusters": ["${cluster}"],
            "rate": "3000",
            "payload": "1024",
            "connections": "1",
            "duration": "30m",
            "max_retries": "3"
         },
         {
            "id": "T03",
            "clusters": ["${cluster}"],
            "rate": "2000",
            "payload": "5120",
            "connections": "1",
            "duration": "30m",
            "max_retries": "3"
         },
         {
            "id": "T04",
            "clusters": ["${cluster}"],
            "rate": "20000",
            "payload": "1024",
            "connections": "1",
            "duration": "30m",
            "max_retries": "3"
         }
    ]
}
EOF

cd ..
chown -R ubuntu: test
