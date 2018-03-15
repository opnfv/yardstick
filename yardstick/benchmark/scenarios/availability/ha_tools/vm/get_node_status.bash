#!/bin/bash

##############################################################################
# Copyright (c) 2018 CMRI and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# check the status of a openstack command

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

source /root/openrc

node_status=$(openstack ${SECURE} compute service list | grep "$1" | awk '{print $12}')

echo "****************$1-status:$node_status****************"

