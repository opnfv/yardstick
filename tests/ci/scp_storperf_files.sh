#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Copy storperf_admin-rc to deployment location.

ssh_options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

if [ "$NODE_NAME" == "huawei-pod1" ]; then
    export INSTALLER_IP='192.168.10.6'
elif [ "$NODE_NAME" == "huawei-pod2" ]; then
    export INSTALLER_IP='192.168.11.2'
fi

sshpass -p root scp 2>/dev/null $ssh_options ~/storperf_admin-rc \
        root@${INSTALLER_IP}:/root/ &> /dev/null
sshpass -p root scp 2>/dev/null $ssh_options /home/opnfv/repos/storperf/docker-compose/docker-compose.yaml \
        root@${INSTALLER_IP}:/root/ &> /dev/null
sshpass -p root scp 2>/dev/null $ssh_options /home/opnfv/repos/storperf/docker-compose/nginx.conf \
        root@${INSTALLER_IP}:/root/ &> /dev/null
