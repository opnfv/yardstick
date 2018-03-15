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

host=$(openstack ${SECURE} server show $1 | grep 'hypervisor_hostname' | awk '{print$4}')

ip=$(openstack ${SECURE} server show $1 | grep 'addresses' | awk '{print$4,$5}')

id=$(openstack ${SECURE} server show $1 | grep 'id' | head -1 | awk '{print$4}')

echo "****************vm-host:$host****************vm-ip:$ip****************vm-id:$id****************"

