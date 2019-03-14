#!/bin/bash
hostIp=$(hostname -I | awk '{print $1}')
kafka0="192.168.1.10"
nats0="192.168.1.20"
test0="192.168.1.100"
test1="192.168.1.101"

if [ "${hostIp}" == "${kafka0}" ] || [ "${hostIp}" == "${test0}"]; then
    cluster="kafka"
else
    cluster="nats"
fi

function pingLoop() {
    local target=${1}
    for payload in 256 1024 5120; do
        sudo ping -i 0.1 -s ${payload} -c 1000 ${target} > env_ping_${cluster}_${payload}.txt
    done
}

if [ "${hostIp}" == "${test0}" ]; then
    pingLoop ${kafka0}
elif [ "${hostIp}" == "${test1}" ]; then
    pingLoop ${nats0}
fi

if [ "${hostIp}" == "${kafka0}" ] || [ "${hostIp}" == "${nats0}" ]; then
    iperf -s -D
else
    if [ "${hostIp}" == "${test0}" ]; then
        iperf -c ${kafka0} -t 300 > env_iperf_${cluster}.txt
    else
        iperf -c ${nats0} -t 300 > env_iperf_${cluster}.txt
    fi
fi

if [ "${hostIp}" == "${kafka0}" ]; then
    # T01 (256 bytes, 1800s, 3000 msg/s)
    dd if=/dev/zero of=/data/speedtest bs=256 count=5400000 2> env_T01_write.txt
    dd if=/data/speedtest of=/dev/zero bs=256 2> env_T01_read.txt
    rm /data/speedtest

    # T02 (1024 bytes, 1800s, 3000 msg/s)
    dd if=/dev/zero of=/data/speedtest bs=1024 count=5400000 2> env_T02_write.txt
    dd if=/data/speedtest of=/dev/zero bs=1024 2> env_T02_read.txt
    rm /data/speedtest

    # T03 (5120 bytes, 1800s, 2000 msg/s)
    dd if=/dev/zero of=/data/speedtest bs=5120 count=3600000 2> env_T03_write.txt
    dd if=/data/speedtest of=/dev/zero bs=5120 2> env_T03_read.txt
    rm /data/speedtest

    # T04 (1024 bytes, 1800s, 20000 msg/s)
    dd if=/dev/zero of=/data/speedtest bs=1024 count=3600000 2> env_T04_write.txt
    dd if=/data/speedtest of=/dev/zero bs=1024 2> env_T04_read.txt
fi