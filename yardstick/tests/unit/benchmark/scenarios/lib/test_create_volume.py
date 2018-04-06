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
from yardstick.benchmark.scenarios.lib import create_volume


class CreateVolumeTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_create_volume = mock.patch.object(
            openstack_utils, 'create_volume')
        self.mock_create_volume = (
            self._mock_create_volume.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(create_volume, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'size': 1}}
        self.result = {}

        self.cvolume_obj = create_volume.CreateVolume(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_create_volume.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        _uuid = uuidutils.generate_uuid()
        self.cvolume_obj.scenario_cfg = {'output': 'id'}
        self.mock_create_volume.return_value = {'name': 'yardstick_volume',
                                                'id': _uuid,
                                                'status': 'available'}
        output = self.cvolume_obj.run(self.result)
        self.assertDictEqual({'volume_create': 1}, self.result)
        self.assertDictEqual({'id': _uuid}, output)
        self.mock_log.info.asset_called_once_with('Create volume successful!')

    def test_run_fail(self):
        self.mock_create_volume.return_value = None
        with self.assertRaises(exceptions.ScenarioCreateVolumeError):
            self.cvolume_obj.run(self.result)
        self.assertDictEqual({'volume_create': 0}, self.result)
        self.mock_log.error.assert_called_once_with('Create volume failed!')
