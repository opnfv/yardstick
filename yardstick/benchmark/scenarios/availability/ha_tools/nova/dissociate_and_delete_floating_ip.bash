#!/bin/bash

##############################################################################
# Copyright (c) 2018 Intracom Telecom and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# dissociate and delete floating ip from server
# parameters: $1 - server name

set -e

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

FLOATINGIP="$(openstack ${SECURE} server list -f value | grep $1 | awk '{print $5}')"
FLOATINGIP_ID="$(openstack ${SECURE} floating ip list -f value | grep ${FLOATINGIP} | awk '{print $1}')"

openstack ${SECURE} server remove floating ip $1 ${FLOATINGIP}
openstack ${SECURE} floating ip delete ${FLOATINGIP_ID}

