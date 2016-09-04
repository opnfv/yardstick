#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
cp /etc/neutron/plugins/ml2/ml2_conf.ini_bkp /etc/neutron/plugins/ml2/ml2_conf.ini

service neutron-l3-agent restart
service neutron-dhcp-agent restart
service neutron-metadata-agent restart
service neutron-server restart
service nova-api restart
service nova-cert restart
service nova-conductor restart
service nova-consoleauth restart
service nova-novncproxy restart
service nova-scheduler restart
service nova-compute restart
