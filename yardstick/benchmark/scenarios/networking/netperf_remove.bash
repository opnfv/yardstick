#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e
echo "===Remove netperf after install begin!==="
cp /etc/apt/sources.list_bkp /etc/apt/sources.list
cp /etc/resolv.conf_bkp /etc/resolv.conf

service netperf stop

sudo apt-get purge -y netperf

echo "===Remove netperf after install end!!!==="
