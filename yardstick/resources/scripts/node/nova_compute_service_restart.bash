#!/bin/bash

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Restart nova-compute.service

set -e

if which systemctl 2>/dev/null; then
  if [ $(systemctl is-active nova-compute.service) == "active" ]; then
      echo "restarting nova-compute.service"
      systemctl restart nova-compute.service
  elif [ $(systemctl is-active openstack-nova-compute.service) == "active" ]; then
      echo "restarting openstack-nova-compute.service"
      systemctl restart openstack-nova-compute.service
  fi
else
  if [[ $(service nova-compute status | grep running) ]]; then
    echo "restarting nova-compute.service"
    service nova-compute restart
  elif [[ $(service openstack-nova-compute status | grep running) ]]; then
    echo "restarting openstack-nova-compute.service"
    service openstack-nova-compute restart
  fi
fi
