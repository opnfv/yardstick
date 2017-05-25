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
    killall -9 -u $process_name 
else
    for pid in `ps aux | grep "/usr/.*/${process_name}" | grep -v grep | grep -v /bin/sh | awk '{print $2}'`; \
        do
            kill -9 ${pid}
        done
fi
