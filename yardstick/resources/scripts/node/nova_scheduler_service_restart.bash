#!/bin/bash

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Restart nova-scheduler.service

set -e

if which systemctl 2>/dev/null; then
  if [ $(systemctl is-active nova-scheduler.service) == "active" ]; then
      echo "restarting nova-scheduler.service"
      systemctl restart nova-scheduler.service
  elif [ $(systemctl is-active openstack-nova-scheduler.service) == "active" ]; then
      echo "restarting openstack-nova-scheduler.service"
      systemctl restart openstack-nova-scheduler.service
  fi
else
  if [[ $(service nova-scheduler status | grep running) ]]; then
    echo "restarting nova-scheduler.service"
    service nova-scheduler restart
  elif [[ $(service openstack-nova-scheduler status | grep running) ]]; then
    echo "restarting openstack-nova-scheduler.service"
    service openstack-nova-scheduler restart
  fi
fi
