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

openstack  ${SECURE} server show $1 | grep 'hypervisor_hostname' | awk '{print$4}'

