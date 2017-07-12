#!/bin/sh

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# check the status of a service

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

   echo $(($(lxc-attach -n "${container_1}" -- ps aux | grep -e "${NOVA_API_PROCESS_1}" | grep -v grep | grep -cv /bin/sh) + $(lxc-attach -n "${container_2}" -- ps aux | grep -e "${NOVA_API_PROCESS_2}" | grep -v grep | grep -cv /bin/sh)))
else
    container=$(lxc-ls -1 --filter="${lxc_filter}")

    if [ "${process_name}" = "haproxy" ]; then
        ps aux | grep -e "/usr/.*/${process_name}" | grep -v grep | grep -cv /bin/sh
    else
        lxc-attach -n "${container}" -- ps aux | grep -e "${process_name}" | grep -v grep | grep -cv /bin/sh
    fi
fi
