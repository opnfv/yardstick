#!/bin/bash
##############################################################################
# Copyright (c) 2015 Ericsson AB, Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Perepare the environment to run yardstick ci

: ${DEPLOY_TYPE:='bm'} # Can be any of 'bm' (Bare Metal) or 'virt' (Virtual)
: ${INSTALLER_TYPE:='unknown'}
: ${NODE_NAME:='unknown'}
: ${EXTERNAL_NETWORK:='admin_floating_net'}

# Extract network name from EXTERNAL_NETWORK
#  e.g. EXTERNAL_NETWORK='ext-net;flat;192.168.0.2;192.168.0.253;192.168.0.1;192.168.0.0/24'
export EXTERNAL_NETWORK=$(echo $EXTERNAL_NETWORK | cut -f1 -d \;)

# Create openstack credentials
echo "INFO: Creating openstack credentials .."
mkdir -p /etc/yardstick
OPENRC=/etc/yardstick/openstack.creds
INSTALLERS=(apex compass fuel joid)

RC_VAR_EXIST=false
if [ "${OS_AUTH_URL}" -a "${OS_USERNAME}" -a "${OS_PASSWORD}" -a "${EXTERNAL_NETWORK}" ];then
    RC_VAR_EXIST=true
fi

if [ "${RC_VAR_EXIST}" = false ]; then
    if [ ! -f $OPENRC ];then
        # credentials file is not given, check if environment variables are set
        # to get the creds using fetch_os_creds.sh later on
        echo "INFO: Checking environment variables INSTALLER_TYPE and INSTALLER_IP"
        if [ -z ${INSTALLER_TYPE} ]; then
            echo "environment variable 'INSTALLER_TYPE' is not defined."
            exit 1
        elif [[ ${INSTALLERS[@]} =~ ${INSTALLER_TYPE} ]]; then
            echo "INSTALLER_TYPE env variable found: ${INSTALLER_TYPE}"
        else
            echo "Invalid env variable INSTALLER_TYPE=${INSTALLER_TYPE}"
            exit 1
        fi

        if [ "$DEPLOY_TYPE" == "virt" ]; then
            FETCH_CRED_ARG="-v -d $OPENRC -i ${INSTALLER_TYPE} -a ${INSTALLER_IP}"
        else
            FETCH_CRED_ARG="-d $OPENRC -i ${INSTALLER_TYPE} -a ${INSTALLER_IP}"
        fi

        $RELENG_REPO_DIR/utils/fetch_os_creds.sh $FETCH_CRED_ARG
    fi
    source $OPENRC
fi

export EXTERNAL_NETWORK INSTALLER_TYPE DEPLOY_TYPE NODE_NAME

# Prepare a admin-rc file for StorPerf integration
$YARDSTICK_REPO_DIR/tests/ci/prepare_storperf_admin-rc.sh

# copy Storperf related files to the deployment location
if [ "$INSTALLER_TYPE" == "compass" ]; then
    source $YARDSTICK_REPO_DIR/tests/ci/scp_storperf_files.sh
fi

# Fetching id_rsa file from jump_server..."
verify_connectivity() {
    local ip=$1
    echo "Verifying connectivity to $ip..."
    for i in $(seq 0 10); do
        if ping -c 1 -W 1 $ip > /dev/null; then
            echo "$ip is reachable!"
            return 0
        fi
        sleep 1
    done
    error "Can not talk to $ip."
}

ssh_options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

if [ "$INSTALLER_TYPE" == "fuel" ]; then
    #ip_fuel="10.20.0.2"
    verify_connectivity $INSTALLER_IP
    echo "Fetching id_rsa file from jump_server $INSTALLER_IP..."
    sshpass -p r00tme scp 2>/dev/null $ssh_options \
    root@${INSTALLER_IP}:~/.ssh/id_rsa /root/.ssh/id_rsa &> /dev/null

    sshpass -p r00tme ssh 2>/dev/null $ssh_options \
        root@${INSTALLER_IP} fuel node>fuel_node

    # update fuel node id and ip info according to the CI env
    controller_IDs=($(cat fuel_node|grep controller|awk '{print $1}'))
    compute_IDs=($(cat fuel_node|grep compute|awk '{print $1}'))
    controller_ips=($(cat fuel_node|grep controller|awk '{print $10}'))
    compute_ips=($(cat fuel_node|grep compute|awk '{print $10}'))

    pod_yaml="./etc/yardstick/nodes/fuel_baremetal/pod.yaml"
    node_line_num=($(grep -n node[1-5] $pod_yaml | awk -F: '{print $1}'))

    if [[ ${controller_ips[0]} ]]; then
        sed -i "${node_line_num[0]}s/node1/node${controller_IDs[0]}/;s/ip1/${controller_ips[0]}/" $pod_yaml;
    fi
    if [[ ${controller_ips[1]} ]]; then
        sed -i "${node_line_num[1]}s/node2/node${controller_IDs[1]}/;s/ip2/${controller_ips[1]}/" $pod_yaml;
    fi
    if [[ ${controller_ips[2]} ]]; then
        sed -i "${node_line_num[2]}s/node3/node${controller_IDs[2]}/;s/ip3/${controller_ips[2]}/" $pod_yaml;
    fi
    if [[ ${compute_ips[0]} ]]; then
        sed -i "${node_line_num[3]}s/node4/node${compute_IDs[0]}/;s/ip4/${compute_ips[0]}/" $pod_yaml;
    fi
    if [[ ${compute_ips[1]} ]]; then
        sed -i "${node_line_num[4]}s/node5/node${compute_IDs[1]}/;s/ip5/${compute_ips[1]}/" $pod_yaml;
    fi

fi
