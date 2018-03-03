#!/bin/bash

##############################################################################
# Copyright (c) 2018 Intracom Telecom and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# create nova server
# parameters: $1 - server name, $2 - image name, $3 - flavor name, $4 - network name

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

NETNAME="$(openstack ${SECURE} network list -f value | grep $4 | awk '{print $2}')"

openstack ${SECURE} server create $1 --image $2 --flavor $3 --network ${NETNAME}

