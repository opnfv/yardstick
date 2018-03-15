#!/bin/bash

##############################################################################
# (c) OPNFV, Wang Meng and others.
# mengwang@bupt.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# check vm status
# parameter: $1 - vm name

set -e

source /root/openrc

if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
    SECURE="--insecure"
else
    SECURE=""
fi

sleep $2

nova ${SECURE} list | grep "$1" | awk '{print$10}'


