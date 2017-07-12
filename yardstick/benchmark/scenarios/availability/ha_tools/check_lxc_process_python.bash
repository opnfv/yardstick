#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# check the status of a service

set -e

process_name=$1

lxc_filter=${service_name//-/_}

container=$(lxc-ls -1 --filter="${lxc_filter}")

lxc-attach -n "${container}" -- ps aux | grep -e "${process_name}" | grep -v grep | grep -cv /bin/sh
