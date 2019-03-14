#!/bin/bash
function wait_for_pids {
    local PIDS="$*"
    local DELAY_BETWEEN_RETRIES_IN_SECONDS=5
    local MAX_RETRIES=60
    echo "Checking PID ${PIDS}"
    set +e
    for i in $(seq 1 ${MAX_RETRIES}); do
        if ! ps -p ${PIDS} > /dev/null ; then
            break
        fi
        sleep ${DELAY_BETWEEN_RETRIES_IN_SECONDS}
    done
    set -e
}

function wait_for_disk {
    local device_name=${1}
    local DELAY_BETWEEN_RETRIES_IN_SECONDS=5
    local MAX_RETRIES=60
    set +e
    for i in $(seq 1 ${MAX_RETRIES}); do
        if lsblk -o NAME | grep -q ${device_name} ; then
            break
        fi
        sleep ${DELAY_BETWEEN_RETRIES_IN_SECONDS}
    done
    set -e
}

function leading_zero {
    printf "%.2d" "${1}"
}