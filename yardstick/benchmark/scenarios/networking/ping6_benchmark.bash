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

installer_type=$1
shift
ping_options="$@"

if [ "$installer_type" == 'compass' ]; then
    source /opt/admin-openrc.sh
elif [ "$installer_type" == 'fuel' ]; then
    source openrc
elif [ "$installer_type" == 'apex' ]; then
    echo "hello"
elif [ "$installer_type" == 'joid' ]; then
    echo "Do nothing, creds will be provided through volume option at docker creation for joid"
else
    echo "$installer_type is not supported by this script"
    exit 0
fi
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
sudo ip netns exec qdhcp-$(neutron net-list | grep -w ipv4-int-network1 | awk '{print $2}') ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i vRouterKey fedora@20.0.0.4 "ping6 $ping_options 2001:db8:0:1::1 | grep ttl | awk -F [=\ ] '{printf \$10}'"
