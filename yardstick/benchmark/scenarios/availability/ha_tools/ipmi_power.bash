#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Stop a service and check the service is stoped

set -e

ipmi_ip=$1
ipmi_user=$2
ipmi_pwd=$3

action=$4
ipmitool -I lanplus -H $ipmi_ip -U $ipmi_user -P $ipmi_pwd power $action
