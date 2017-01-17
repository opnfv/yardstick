##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from pyroute2 import IPDB


# configuration for influxdb
with IPDB() as ip:
    GATEWAY_IP = ip.routes['default'].gateway
PORT = 8086

TEST_CASE_PATH = '../tests/opnfv/test_cases/'

SAMPLE_PATH = '../samples/'

TEST_CASE_PRE = 'opnfv_yardstick_'

TEST_SUITE_PATH = '../tests/opnfv/test_suites/'

TEST_SUITE_PRE = 'opnfv_'

OUTPUT_CONFIG_FILE_PATH = '/etc/yardstick/yardstick.conf'
