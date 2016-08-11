#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
set -e

installer_type=$1

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

host_num=$(neutron dhcp-agent-list-hosting-net ipv4-int-network1 | grep True | awk -F [=\ ] '{printf $4}') > /tmp/ipv6.log
echo $host_num
