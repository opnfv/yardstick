#!/bin/bash

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

process_name=$1

lxc_filter=$(echo ${process_name} | sed 's/-/_/g')

container=$(lxc-ls -1 --filter=${lxc_filter})

if [ "$process_name" = "keystone" ]; then
    pids=$(lxc-attach -n ${container} -- ps aux | grep "keystone" | grep -iv heartbeat | grep -iv monitor | grep -v grep | grep -v /bin/sh | awk '{print $2}')
    for pid in ${pids};
        do
            kill -9 "${pid}"
        done
else
    pids=$(lxc-attach -n ${container} -- pgrep -f "/openstack/.*/${process_name}")
    for pid in ${pids};
    do
        lxc-attach -n ${container} -- kill -9 "${pid}"
    done
fi
