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
from yardstick.benchmark.scenarios.lib import attach_volume


class AttachVolumeTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_attach_volume_to_server = mock.patch.object(
            openstack_utils, 'attach_volume_to_server')
        self._mock_attach_volume_to_server = (
            self._mock_attach_volume_to_server.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(attach_volume, 'LOG')
        self.mock_log = self._mock_log.start()
        _uuid = uuidutils.generate_uuid()
        self.args = {'options': {'server_id': _uuid, 'volume_id': _uuid}}
        self.result = {}

        self.attachvol_obj = attach_volume.AttachVolume(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_attach_volume_to_server.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self._mock_attach_volume_to_server.return_value = True
        self.assertIsNone(self.attachvol_obj.run(self.result))
        self.assertEqual({'attach_volume': 1}, self.result)
        self.mock_log.info.asset_called_once_with(
            'Attach volume to server successful!')

    def test_run_fail(self):
        self._mock_attach_volume_to_server.return_value = None
        with self.assertRaises(exceptions.ScenarioAttachVolumeError):
            self.attachvol_obj.run(self.result)
        self.assertEqual({'attach_volume': 0}, self.result)
        self.mock_log.error.assert_called_once_with(
            'Attach volume to server failed!')
