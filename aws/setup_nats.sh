#!/bin/bash
set -e
source helper.sh

## Download necessary packages
sudo apt-get -qq update && sudo apt-get -qq install iperf unzip -y > /dev/null 2>&1
wget --tries=10 https://github.com/nats-io/gnatsd/releases/download/v1.4.1/gnatsd-v1.4.1-linux-amd64.zip
unzip gnatsd-v1.4.1-linux-amd64.zip
sudo chown -R ubuntu: gnatsd-v1.4.1-linux-amd64
cd gnatsd-v1.4.1-linux-amd64

sudo cat <<EOF | sudo tee -a /etc/hosts > /dev/null
192.168.2.10    bastion0
EOF

sleep 5
nohup ./gnatsd &
sleep 5

while ! $(ss -lnt | grep -q 4222); do
    nohup ./gnatsd &
    sleep 5
    echo "not started"
done
