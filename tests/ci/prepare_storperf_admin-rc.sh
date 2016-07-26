#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

AUTH_URL=${OS_AUTH_URL}
USERNAME=${OS_USERNAME:-admin}
PASSWORD=${OS_PASSWORD:-console}
TENANT_NAME=${OS_TENANT_NAME:-admin}
VOLUME_API_VERSION=${OS_VOLUME_API_VERSION:-2}
PROJECT_NAME=${OS_PROJECT_NAME:-$TENANT_NAME}
TENANT_ID=`keystone tenant-get admin|grep 'id'|awk -F '|' '{print $3}'|sed -e 's/^[[:space:]]*//'`


rm -f ~/storperf_admin-rc
touch ~/storperf_admin-rc

echo "OS_AUTH_URL="$AUTH_URL >> ~/storperf_admin-rc
echo "OS_USERNAME="$USERNAME >> ~/storperf_admin-rc
echo "OS_PASSWORD="$PASSWORD >> ~/storperf_admin-rc
echo "OS_TENANT_NAME="$TENANT_NAME >> ~/storperf_admin-rc
echo "OS_VOLUME_API_VERSION="$VOLUME_API_VERSION >> ~/storperf_admin-rc
echo "OS_PROJECT_NAME="$PROJECT_NAME >> ~/storperf_admin-rc
echo "OS_TENANT_ID="$TENANT_ID >> ~/storperf_admin-rc
