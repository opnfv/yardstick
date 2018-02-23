##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import unittest
import mock

from yardstick.benchmark.scenarios.lib import create_floating_ip
from yardstick.common import openstack_utils
from yardstick.common import exceptions


class CreateFloatingIpTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_create_floating_ip = mock.patch.object(
            openstack_utils, 'create_floating_ip')
        self.mock_create_floating_ip = self._mock_create_floating_ip.start()
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(create_floating_ip, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'network_name_or_id': 'yardstick_net'}}
        self.result = {}

        self._fip_obj = create_floating_ip.CreateFloatingIp(self.args, mock.ANY)
        self._fip_obj.scenario_cfg = {'output': 'key1\nkey2'}

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_create_floating_ip.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_create_floating_ip.return_value = {'fip_id': 'value1',
                                                     'fip_addr': 'value2'}
        output = self._fip_obj.run(self.result)
        self.assertEqual({"floating_ip_create": 1}, self.result)
        self.assertEqual({'key1': 'value1', 'key2': 'value2'}, output)
        self.mock_log.info.asset_called_once_with(
            'Creating floating ip successful!')

    def test_run_no_fip(self):
        self.mock_create_floating_ip.return_value = None
        with self.assertRaises(exceptions.ScenarioCreateFloatingIPError):
            self._fip_obj.run(self.result)
        self.assertEqual({"floating_ip_create": 0}, self.result)
        self.mock_log.error.assert_called_once_with(
            'Creating floating ip failed!')
