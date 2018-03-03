#!/bin/bash

##############################################################################
# Copyright (c) 2018 Intracom Telecom and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# add floating ip to server
# parameter: $1 - server name, $2 - external network name

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

FLOATINGIP="$(openstack ${SECURE} floating ip create -f value $2 | awk 'NR==4')"

openstack ${SECURE} server add floating ip $1 ${FLOATINGIP}

