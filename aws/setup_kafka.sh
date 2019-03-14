#!/bin/bash
set -e
source helper.sh

masterIp="192.168.1.10"
hostIp=$(hostname -i | awk '{print $1}')
## Download necessary packages
sudo apt-get -qq update && sudo apt-get -qq install iperf default-jre -y > /dev/null 2>&1
wget --tries=10 https://www-eu.apache.org/dist/kafka/2.1.0/kafka_2.12-2.1.0.tgz
tar xvf kafka_2.12-2.1.0.tgz
cd kafka_2.12-2.1.0

sudo sed -i 's|/tmp/kafka-logs|/data/kafka-logs|' config/server.properties
sudo sed -i 's|/tmp/zookeeper|/data/zookeeper|' config/zookeeper.properties

wait_for_disk "xvdf"
sudo parted -s -a optimal /dev/xvdf mklabel gpt -- mkpart primary xfs 0% 100%
sleep 2
sudo mkfs.xfs -q /dev/xvdf1
sudo mkdir /data
echo "/dev/xvdf1              /data    xfs    defaults                0 2" | sudo tee -a /etc/fstab
sudo mount -a
chown -R ubuntu: /data

sudo cat <<EOF | sudo tee -a /etc/hosts > /dev/null
192.168.2.10    bastion0
EOF

nohup sudo bin/zookeeper-server-start.sh config/zookeeper.properties &

sleep 5
nohup sudo bin/kafka-server-start.sh config/server.properties &
