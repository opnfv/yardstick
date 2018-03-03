#!/bin/bash

##############################################################################
# Copyright (c) 2018 Intracom Telecom and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# remove server from existing security group
# parameters: $1 - server name, $2 - security group name

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

SECGROUPNAME="$(openstack ${SECURE} security group list -f value | grep $2 | awk '{print $2}')"

openstack ${SECURE} server remove security group $1 ${SECGROUPNAME}
