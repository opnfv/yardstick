#!/bin/bash

##############################################################################
# (c) OPNFV, Yin Kanglin and others.
# 14_ykl@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# create flavor
# parameter: $1-name $2-id $3-ram $4-disk $5-vcpus

set -e

source /root/openrc

nova flavor-create $1 $2 $3 $4 $5
