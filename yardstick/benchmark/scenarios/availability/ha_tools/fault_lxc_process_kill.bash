#!/bin/sh

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Stop process by process name

set -e

NOVA_API_PROCESS_1="nova-api-os-compute"
NOVA_API_PROCESS_2="nova-api-metadata"
NOVA_API_LXC_FILTER_1="nova_api_os_compute"
NOVA_API_LXC_FILTER_2="nova_api_metadata"

process_name=$1

lxc_filter=$(echo "${process_name}" | sed 's/-/_/g')

if [ "${lxc_filter}" = "glance_api" ]; then
    lxc_filter="glance"
fi

if [ "${process_name}" = "nova-api" ]; then
    container_1=$(lxc-ls -1 --filter="${NOVA_API_LXC_FILTER_1}")
    container_2=$(lxc-ls -1 --filter="${NOVA_API_LXC_FILTER_2}")

    pids_1=$(lxc-attach -n "${container_1}" -- pgrep -f "/openstack/.*/${NOVA_API_PROCESS_1}")
    for pid in ${pids_1};
        do
            lxc-attach -n "${container_1}" -- kill -9 "${pid}"
        done

    pids_2=$(lxc-attach -n "${container_2}" -- pgrep -f "/openstack/.*/${NOVA_API_PROCESS_2}")
    for pid in ${pids_2};
        do
            lxc-attach -n "${container_2}" -- kill -9 "${pid}"
        done
else
    container=$(lxc-ls -1 --filter="${lxc_filter}")

    if [ "${process_name}" = "haproxy" ]; then
        for pid in $(pgrep -cf "/usr/.*/${process_name}");
            do
                kill -9 "${pid}"
            done
    elif [ "${process_name}" = "keystone" ]; then
        pids=$(lxc-attach -n "${container}" -- ps aux | grep "keystone" | grep -iv heartbeat | grep -iv monitor | grep -v grep | grep -v /bin/sh | awk '{print $2}')
        for pid in ${pids};
            do
                lxc-attach -n "${container}" -- kill -9 "${pid}"
            done
    else
        pids=$(lxc-attach -n "${container}" -- pgrep -f "/openstack/.*/${process_name}")
        for pid in ${pids};
            do
                lxc-attach -n "${container}" -- kill -9 "${pid}"
            done
    fi
fi
