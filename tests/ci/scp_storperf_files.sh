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
sshpass -p root scp 2>/dev/null $ssh_options ~/storperf_admin-rc \
        root@192.168.200.1:/root/ &> /dev/null
sshpass -p root scp 2>/dev/null $ssh_options /home/opnfv/repos/yardstick/resources/storperf/docker-compose.yaml \
        root@192.168.200.1:/root/ &> /dev/null
sshpass -p root scp 2>/dev/null $ssh_options /home/opnfv/repos/yardstick/resources/storperf/nginx.conf \
        root@192.168.200.1:/root/ &> /dev/null
