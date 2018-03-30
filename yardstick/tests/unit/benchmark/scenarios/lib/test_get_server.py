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
from yardstick.benchmark.scenarios.lib import get_server


class GetServerTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_get_server = mock.patch.object(
            openstack_utils, 'get_server')
        self.mock_get_server = self._mock_get_server.start()
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(get_server, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'server_name_or_id': 'yardstick_key'}}
        self.result = {}

        self.getserver_obj = get_server.GetServer(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_get_server.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        _uuid = uuidutils.generate_uuid()
        self.getserver_obj.scenario_cfg = {'output': 'id'}
        self.mock_get_server.return_value = {
            'server': {'name': 'key-name', 'id': _uuid}}
        output = self.getserver_obj.run(self.result)
        self.assertDictEqual({'get_server': 1}, self.result)
        self.assertDictEqual({'id': _uuid}, output)
        self.mock_log.info.asset_called_once_with('Get Server successful!')

    def test_run_fail(self):
        self.mock_get_server.return_value = None
        with self.assertRaises(exceptions.ScenarioGetServerError):
            self.getserver_obj.run(self.result)
        self.assertDictEqual({'get_server': 0}, self.result)
        self.mock_log.error.assert_called_once_with('Get Server failed!')
