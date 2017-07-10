#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# StorPerf plugin un-installation script

set -e

export TAG=${DOCKER_TAG:-latest}
export ENV_FILE=~/storperf_admin-rc
export CARBON_DIR=~/carbon

rm -rf "${CARBON_DIR}"

docker-compose down

for container_name in storperf swagger-ui http-front-end
do
    container=$(docker ps -a -q -f name=$container_name)
    if [[ ! -z $container ]]
    then
        echo "Stopping any existing $container_name container"
        docker rm -fv $container
    fi
done
