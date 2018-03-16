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
from yardstick.common import exceptions
from yardstick.benchmark.scenarios.lib import create_sec_group


class CreateSecurityGroupTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_create_security_group_full = mock.patch.object(
            openstack_utils, 'create_security_group_full')
        self.mock_create_security_group_full = (
            self._mock_create_security_group_full.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(create_sec_group, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'sg_name': 'yardstick_net'}}
        self.result = {}

        self.csecgp_obj = create_sec_group.CreateSecgroup(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_create_security_group_full.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        _uuid = uuidutils.generate_uuid()
        self.csecgp_obj.scenario_cfg = {'output': 'id'}
        self.mock_create_security_group_full.return_value = _uuid
        output = self.csecgp_obj.run(self.result)
        self.assertEqual({"sg_create": 1}, self.result)
        self.assertEqual({'id': _uuid}, output)
        self.mock_log.info.asset_called_once_with(
            "Create security group successful!")

    def test_run_fail(self):
        self.mock_create_security_group_full.return_value = None
        with self.assertRaises(exceptions.ScenarioCreateSecurityGroupError):
            self.csecgp_obj.run(self.result)
        self.assertEqual({"sg_create": 0}, self.result)
        self.mock_log.error.assert_called_once_with(
            "Create security group failed!")
