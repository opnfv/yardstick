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

svc="netserver"
if pgrep $svc >/dev/null
then
    echo "$svc have existed, exit!"
    exit 0
fi

echo "===Install netperf before test begin!!!==="
cp /etc/apt/sources.list /etc/apt/sources.list_bkp
cp /etc/resolv.conf /etc/resolv.conf_bkp
echo "nameserver 8.8.4.4" >> /etc/resolv.conf

cat <<EOF >/etc/apt/sources.list
deb http://archive.ubuntu.com/ubuntu/ trusty main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ trusty-security main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ trusty-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ trusty-proposed main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ trusty-backports main restricted universe multiverse
EOF

sudo apt-get update
sudo apt-get install -y netperf

service netperf start

echo "===Install netperf before test end!!!==="

