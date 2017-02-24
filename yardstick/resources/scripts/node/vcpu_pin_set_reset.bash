#!/bin/bash

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Reset vcpu_pin_set and reserved_host_memory_mb

set -e

sed -i '/vcpu_pin_set/d' /etc/nova/nova.conf
sed -i '/reserved_host_memory_mb/d' /etc/nova/nova.conf
