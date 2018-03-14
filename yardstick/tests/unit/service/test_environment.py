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
from yardstick.service.environment import AnsibleCommon
from yardstick.common.exceptions import UnsupportedPodFormatError


class EnvironmentTestCase(unittest.TestCase):

    def test_get_sut_info(self):
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

        AnsibleCommon.gen_inventory_ini_dict = mock.MagicMock()
        AnsibleCommon.get_sut_info = mock.MagicMock(return_value={'node1': {}})

        env = Environment(pod=pod_info)
        env.get_sut_info()

    def test_get_sut_info_pod_str(self):
        pod_info = 'nodes'

        env = Environment(pod=pod_info)
        with self.assertRaises(UnsupportedPodFormatError):
            env.get_sut_info()


if __name__ == '__main__':
    unittest.main()
