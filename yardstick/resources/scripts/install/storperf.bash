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
#     1. docker and docker-compose have been installed on the Jump Host
#     2. Openstack environment file for storperf, '~/storperf_admin-rc', is ready
#     3. Jump Host must have internet connectivity for downloading docker image
#     4. Jump Host has access to the OpenStack Controller API
#     5. Enough OpenStack floating IPs must be available to match your agent count
#     6. The following ports are exposed if you use the supplied docker-compose.yaml file:
#        * 5000 for StorPerf ReST API and Swagger UI
#        * 8000 for StorPerf's Graphite Web Server

set -e

WWW_DATA_UID=33
WWW_DATA_GID=33

export TAG=${DOCKER_TAG:-latest}
export ENV_FILE=~/storperf_admin-rc
export CARBON_DIR=~/carbon

sudo install --owner=${WWW_DATA_UID} --group=${WWW_DATA_GID} -d "${CARBON_DIR}"

docker-compose -f ~/docker-compose.yaml pull
docker-compose -f ~/docker-compose.yaml up -d
