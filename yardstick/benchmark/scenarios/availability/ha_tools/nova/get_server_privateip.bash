#!/bin/bash

##############################################################################
# Copyright (c) 2018 Intracom Telecom and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# get private ip of a server
# parameter: $1 - server name

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

openstack ${SECURE} server list -f value -c Name -c Networks | grep $1 | awk '{print $2}' | sed -r 's/.*=([0-9\.\:]+)[;,]*/\1/'

