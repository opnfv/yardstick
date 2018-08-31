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

if [ "$process_name" = "keystone" ]; then
    for pid in $(ps aux | grep "keystone" | grep -iv monitor | grep -v grep | grep -v /bin/sh | awk '{print $2}'); \
        do
            kill -9 "${pid}"
        done
elif [ "$process_name" = "haproxy" ]; then
    for pid in $(pgrep -f "^/usr/[^ ]*/${process_name}");
        do
            kill -9 "${pid}"
        done
else
    for pid in $(pgrep -fa [^-_a-zA-Z0-9]${process_name} | grep -iv heartbeat | awk '{print $1}');
        do
            kill -9 "${pid}"
        done
fi
