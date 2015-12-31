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


sudo ip netns exec qdhcp-$(neutron net-list | grep -w ipv4-int-network1 | awk '{print $2}') bash
# TODO ip  
ssh -i vRouterkey fedora@20.0.0.4
ping6 -c 1 2001:db8:0:1::1 | grep ttl | awk -F [=\ ] '{printf $10}'
