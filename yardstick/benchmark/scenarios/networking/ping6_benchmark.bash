#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a single ping6 command towards a ipv6 router
set -e
source /opt/admin-openrc.sh
chmod 600 vRouterKey
# TODO find host
wait_vm_ok() {
    retry=0
    until timeout 100s sudo ip netns exec qdhcp-$(neutron net-list | grep -w ipv4-int-network1 | awk '{print $2}') ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i vRouterKey fedora@20.0.0.4  "exit" >/dev/null 2>&1
    do
        sleep 10
        let retry+=1
        if [ $retry -ge 40 ];
        then
            echo "vm ssh  start timeout !!!"
            exit 0
        fi
    done
}
wait_vm_ok
sleep 360
sudo ip netns exec qdhcp-$(neutron net-list | grep -w ipv4-int-network1 | awk '{print $2}') ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i vRouterKey fedora@20.0.0.4 "ping6 -c 1 2001:db8:0:1::1 | grep ttl | awk -F [=\ ] '{printf \$10}'"