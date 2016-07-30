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

: ${NODE_NAME:='unknown'}
: ${EXTERNAL_NETWORK:='admin_floating_net'}


# Extract network name from EXTERNAL_NETWORK
#  e.g. EXTERNAL_NETWORK='ext-net;flat;192.168.0.2;192.168.0.253;192.168.0.1;192.168.0.0/24'
export EXTERNAL_NETWORK=$(echo $EXTERNAL_NETWORK | cut -f1 -d \;)

# Create openstack credentials
echo "INFO: Creating openstack credentials .."
OPENRC=/home/opnfv/openrc
INSTALLERS=(apex compass fuel joid)

if [ ! -f $OPENRC ]; then
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

export EXTERNAL_NETWORK INSTALLER_TYPE DEPLOY_TYPE NODE_NAME

# Prepare a admin-rc file for StorPerf integration
$YARDSTICK_REPO_DIR/tests/ci/prepare_storperf_admin-rc.sh

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
fi

