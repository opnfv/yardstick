#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
openrc=$*
source $openrc
host_num=$(neutron dhcp-agent-list-hosting-net ipv4-int-network1 | grep True | head -1 | awk -F [=\ ] '{printf $4}' | grep -o '[0-9]\+') > /tmp/ipv6.log
echo "host$host_num"
