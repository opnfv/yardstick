##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest

import mock

from yardstick.service.environment import Environment
from yardstick.common.ansible_common import AnsibleCommon


class EnvironmentTestCase(unittest.TestCase):
    @mock.patch.object(AnsibleCommon, 'gen_inventory_ini_dict')
    @mock.patch.object(AnsibleCommon, 'get_sut_info')
    def test_get_sut_info(self, mock_gen_inventory, mock_get_sut):
        pod_info = {
            'nodes': [
                {
                    'name': 'node1',
                    'host_name': 'host1',
                    'role': 'Controller',
                    'ip': '10.1.0.50',
                    'user': 'root',
                    'passward': 'root'
                }
            ]
        }
        mock_get_sut.return_value = {'node1': {}}

        env = Environment(pod=pod_info)
        env.get_sut_info()
