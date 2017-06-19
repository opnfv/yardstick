#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# StorPerf plugin installation script
# After installation, it will run StorPerf container on Jump Host
# Requirements:
#     1. docker has been installed on the Jump Host
#     2. Openstack environment file for storperf, '~/storperf_admin-rc', is ready.

set -e

mkdir -p /tmp/storperf-yardstick

docker pull opnfv/storperf

STORPERF_DIR=/tmp/storperf-yardstick/carbon
docker run -t \
--env-file ~/storperf_admin-rc \
-p 5000:5000 -p 8000:8000 \
-v $STORPERF_DIR:/opt/graphite/storage/whisper \
--name storperf-yardstick opnfv/storperf &

chown 33:33 $STORPERF_DIR
