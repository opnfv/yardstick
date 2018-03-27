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
from yardstick.benchmark.scenarios.lib import create_keypair


class CreateKeypairTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_create_keypair = mock.patch.object(
            openstack_utils, 'create_keypair')
        self.mock_create_keypair = (
            self._mock_create_keypair.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(create_keypair, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'key_name': 'yardstick_key'}}
        self.result = {}

        self.ckeypair_obj = create_keypair.CreateKeypair(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_create_keypair.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        _uuid = uuidutils.generate_uuid()
        self.ckeypair_obj.scenario_cfg = {'output': 'id'}
        self.mock_create_keypair.return_value = {
            'keypair': {'name': 'key-name', 'type': 'ssh', 'id': _uuid}}
        output = self.ckeypair_obj.run(self.result)
        self.assertDictEqual({'keypair_create': 1}, self.result)
        self.assertDictEqual({'id': _uuid}, output)
        self.mock_log.info.asset_called_once_with('Create keypair successful!')

    def test_run_fail(self):
        self.mock_create_keypair.return_value = None
        with self.assertRaises(exceptions.ScenarioCreateKeypairError):
            self.ckeypair_obj.run(self.result)
        self.assertDictEqual({'keypair_create': 0}, self.result)
        self.mock_log.error.assert_called_once_with('Create keypair failed!')
