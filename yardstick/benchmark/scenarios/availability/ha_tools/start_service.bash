#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Start or restart a service and check the service is started

set -e

service_name=$1
operation=${2:-"start"} # values are "start" or "restart"

Distributor=$(lsb_release -a | grep "Distributor ID" | awk '{print $3}')

if [ "$Distributor" != "Ubuntu" -a "$service_name" != "keystone" -a "$service_name" != "neutron-server" -a "$service_name" != "haproxy" -a "$service_name" != "openvswitch" ]; then
    service_name="openstack-"${service_name}
elif [ "$Distributor" = "Ubuntu" -a "$service_name" = "keystone" ]; then
    service_name="apache2"
elif [ "$service_name" = "keystone" ]; then
    service_name="httpd"
fi

if which systemctl 2>/dev/null; then
    systemctl $operation $service_name
else
    service $service_name $operation
fi
