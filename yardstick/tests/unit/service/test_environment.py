##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock

from yardstick.common import exceptions
from yardstick.service import environment
from yardstick.tests.unit import base as ut_base


class EnvironmentTestCase(ut_base.BaseUnitTestCase):

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

        with mock.patch.object(environment.AnsibleCommon,
                               'gen_inventory_ini_dict'), \
                mock.patch.object(environment.AnsibleCommon, 'get_sut_info',
                                  return_value={'node1': {}}), \
                mock.patch.object(environment.Environment, '_format_sut_info'):
            env = environment.Environment(pod=pod_info)
            env.get_sut_info()

    def test_get_sut_info_pod_str(self):
        pod_info = 'nodes'

        env = environment.Environment(pod=pod_info)
        with self.assertRaises(exceptions.UnsupportedPodFormatError):
            env.get_sut_info()
