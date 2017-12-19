#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Prepare storperf_admin-rc for StorPerf.

AUTH_URL=${OS_AUTH_URL}
USERNAME=${OS_USERNAME:-admin}
PASSWORD=${OS_PASSWORD:-console}

# OS_TENANT_NAME is still present to keep backward compatibility with legacy
# deployments, but should be replaced by OS_PROJECT_NAME.
TENANT_NAME=${OS_TENANT_NAME:-admin}
PROJECT_NAME=${OS_PROJECT_NAME:-$TENANT_NAME}
PROJECT_ID=`openstack project show admin|grep '\bid\b' |awk -F '|' '{print $3}'|sed -e 's/^[[:space:]]*//'`

USER_DOMAIN_ID=${OS_USER_DOMAIN_ID:-default}

rm -f ~/storperf_admin-rc
touch ~/storperf_admin-rc

echo "OS_AUTH_URL="$AUTH_URL >> ~/storperf_admin-rc
echo "OS_USERNAME="$USERNAME >> ~/storperf_admin-rc
echo "OS_PASSWORD="$PASSWORD >> ~/storperf_admin-rc
echo "OS_PROJECT_NAME="$PROJECT_NAME >> ~/storperf_admin-rc
echo "OS_PROJECT_ID="$PROJECT_ID >> ~/storperf_admin-rc
echo "OS_USER_DOMAIN_ID="$USER_DOMAIN_ID >> ~/storperf_admin-rc
echo "OS_PROJECT_DOMAIN_NAME="$OS_PROJECT_DOMAIN_NAME >> ~/storperf_admin-rc
echo "OS_USER_DOMAIN_NAME="$OS_USER_DOMAIN_NAME >> ~/storperf_admin-rc
echo "TEST_DB_URL=http://testresults.opnfv.org/test/api/v1" >> ~/storperf_admin-rc
