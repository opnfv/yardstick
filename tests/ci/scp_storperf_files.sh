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

scp_files(){
    export JUMP_HOST_IP
    sshpass -p root scp 2>/dev/null $ssh_options ~/storperf_admin-rc \
            root@${JUMP_HOST_IP}:/root/ &> /dev/null
    sshpass -p root scp 2>/dev/null $ssh_options /home/opnfv/repos/storperf/docker-compose/docker-compose.yaml \
            root@${JUMP_HOST_IP}:/root/ &> /dev/null
}

case "$NODE_NAME" in
    "huawei-pod1")
        JUMP_HOST_IP='192.168.10.6'
        scp_files
        ;;
    "huawei-pod2")
        JUMP_HOST_IP='192.168.11.2'
        scp_files
        ;;
    *)
        # no node name, exit
        echo "storperf test case will not run on this pod, skipping scp files..."
        ;;
esac
