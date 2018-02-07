##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from oslo_utils import uuidutils
import unittest
import mock

from yardstick.common import openstack_utils
from yardstick.benchmark.scenarios.lib import create_subnet


class CreateSubnetTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_create_neutron_subnet = mock.patch.object(
            openstack_utils, 'create_neutron_subnet')
        self.mock_create_neutron_subnet = \
            self._mock_create_neutron_subnet.start()
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(create_subnet, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'network_name_or_id': 'yardstick_net'}}

        self._csubnet_obj = create_subnet.CreateSubnet(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_create_neutron_subnet.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        _uuid = uuidutils.generate_uuid()
        self._csubnet_obj.scenario_cfg = {'output': 'id'}
        self.mock_create_neutron_subnet.return_value = _uuid
        output = self._csubnet_obj.run()
        self.assertDictEqual({'id': _uuid}, output)
        self.mock_log.info.asset_called_once_with('Create subnet successful!')

    def test_run_fail(self):
        self._csubnet_obj.scenario_cfg = {'output': 'id'}
        self.mock_create_neutron_subnet.return_value = None
        output = self._csubnet_obj.run()
        self.assertEqual(None, output)
        self.mock_log.error.assert_called_once_with('Create subnet failed!')
