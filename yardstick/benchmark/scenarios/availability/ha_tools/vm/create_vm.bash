#!/bin/bash

##############################################################################
# (c) OPNFV, Wang Meng and others.
# mengwang@bupt.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# create vm
# parameter: $1-flavor $2-image $3-subnet $4-keypair $5-name

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

openstack ${SECURE} server create --flavor $1 --image $2 --nic net-id=$3 --key $4 $5

sleep 30

floating_ip=$(openstack ${SECURE} floating ip create ext-net | grep 'floating_ip_address' | awk '{print$4}')

openstack ${SECURE} server add floating ip $5 $floating_ip

sleep 300

