#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Start a service and check the service is started

set -e

NOVA_API_SERVICE_1="nova-api-os-compute"
NOVA_API_SERVICE_2="nova-api-metadata"
NOVA_API_LXC_FILTER_1="nova_api_os_compute"
NOVA_API_LXC_FILTER_2="nova_api_metadata"

service_name=$1

if [ "${service_name}" = "haproxy" ]; then
    if which systemctl 2>/dev/null; then
        systemctl start $service_name
    else
        service $service_name start
    fi
else
    lxc_filter=${service_name//-/_}

    if [ "${lxc_filter}" = "glance_api" ]; then
        lxc_filter="glance"
    fi

    if [ "${service_name}" = "nova-api" ]; then
        container_1=$(lxc-ls -1 --filter="${NOVA_API_LXC_FILTER_1}")
        container_2=$(lxc-ls -1 --filter="${NOVA_API_LXC_FILTER_2}")

        if lxc-attach -n "${container_1}" -- which systemctl 2>/dev/null; then
            lxc-attach -n "${container_1}" -- systemctl start "${NOVA_API_SERVICE_1}"
        else
            lxc-attach -n "${container_1}" -- service "${NOVA_API_SERVICE_1}" start
        fi

        if lxc-attach -n "${container_2}" -- which systemctl 2>/dev/null; then
            lxc-attach -n "${container_2}" -- systemctl start "${NOVA_API_SERVICE_2}"
        else
            lxc-attach -n "${container_2}" -- service "${NOVA_API_SERVICE_2}" start
        fi
    else
        container=$(lxc-ls -1 --filter="${lxc_filter}")

        Distributor=$(lxc-attach -n "${container}" -- lsb_release -a | grep "Distributor ID" | awk '{print $3}')

        if [ "${Distributor}" != "Ubuntu" -a "${service_name}" != "keystone" -a "${service_name}" != "neutron-server" ]; then
            service_name="openstack-"${service_name}
        elif [ "${Distributor}" = "Ubuntu" -a "${service_name}" = "keystone" ]; then
            service_name="apache2"
        elif [ "${service_name}" = "keystone" ]; then
            service_name="httpd"
        fi

        if lxc-attach -n "${container}" -- which systemctl 2>/dev/null; then
            lxc-attach -n "${container}" -- systemctl start "${service_name}"
        else
            lxc-attach -n "${container}" -- service "${service_name}" start
        fi
    fi
fi
