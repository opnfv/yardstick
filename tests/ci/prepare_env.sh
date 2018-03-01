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
: ${USER_NAME:='ubuntu'}
: ${SSH_KEY:='/root/.ssh/id_rsa'}

# Extract network name from EXTERNAL_NETWORK
#  e.g. EXTERNAL_NETWORK='ext-net;flat;192.168.0.2;192.168.0.253;192.168.0.1;192.168.0.0/24'
export EXTERNAL_NETWORK=$(echo $EXTERNAL_NETWORK | cut -f1 -d \;)

# Create openstack credentials
echo "INFO: Creating openstack credentials .."
mkdir -p /etc/yardstick
OPENRC=/etc/yardstick/openstack.creds
INSTALLERS=(apex compass fuel joid)

RC_VAR_EXIST=false
if [[ "${OS_AUTH_URL}" && "${OS_USERNAME}" && "${OS_PASSWORD}" && "${EXTERNAL_NETWORK}" ]];then
    RC_VAR_EXIST=true
fi

if [[ "${RC_VAR_EXIST}" = false && -f ${OPENRC} ]]; then
    . ${OPENRC}
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

    # check the connection
    verify_connectivity $INSTALLER_IP

    pod_yaml="$YARDSTICK_REPO_DIR/etc/yardstick/nodes/fuel_baremetal/pod.yaml"

    # update "ip" according to the CI env
    ssh -l ubuntu ${INSTALLER_IP} -i ${SSH_KEY} ${ssh_options} \
         "sudo salt -C 'ctl* or cmp*' grains.get fqdn_ip4  --out yaml">node_info

    controller_ips=($(cat node_info|awk '/ctl/{getline; print $2}'))
    compute_ips=($(cat node_info|awk '/cmp/{getline; print $2}'))

    if [[ ${controller_ips[0]} ]]; then
        sed -i "s|ip1|${controller_ips[0]}|" $pod_yaml;
    fi
    if [[ ${controller_ips[1]} ]]; then
        sed -i "s|ip2|${controller_ips[1]}|" $pod_yaml;
    fi
    if [[ ${controller_ips[2]} ]]; then
        sed -i "s|ip3|${controller_ips[2]}|" $pod_yaml;
    fi
    if [[ ${compute_ips[0]} ]]; then
        sed -i "s|ip4|${compute_ips[0]}|" $pod_yaml;
    fi
    if [[ ${compute_ips[1]} ]]; then
        sed -i "s|ip5|${compute_ips[1]}|" $pod_yaml;
    fi

    # update 'user' and 'key_filename' according to the CI env
    sed -i "s|node_username|${USER_NAME}|;s|node_keyfile|${SSH_KEY}|" $pod_yaml;

fi
