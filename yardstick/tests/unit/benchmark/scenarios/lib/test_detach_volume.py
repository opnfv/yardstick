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
from yardstick.benchmark.scenarios.lib import detach_volume


class DetachVolumeTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_detach_volume = mock.patch.object(
            openstack_utils, 'detach_volume')
        self.mock_detach_volume = (
            self._mock_detach_volume.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(detach_volume, 'LOG')
        self.mock_log = self._mock_log.start()
        _uuid = uuidutils.generate_uuid()
        self.args = {'options': {'server_dict': {'id': _uuid},
                                 'volume_dict': {'id': _uuid}}}
        self.result = {}

        self.detachvol_obj = detach_volume.DetachVolume(self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_detach_volume.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_detach_volume.return_value = True
        self.assertIsNone(self.detachvol_obj.run(self.result))
        self.assertEqual({'detach_volume': 1}, self.result)
        self.mock_log.info.assert_called_once_with(
            'Detach volume from server successful!')

    def test_run_fail(self):
        self.mock_detach_volume.return_value = False
        with self.assertRaises(exceptions.ScenarioDetachVolumeError):
            self.detachvol_obj.run(self.result)
        self.assertEqual({'detach_volume': 0}, self.result)
        self.mock_log.error.assert_called_once_with(
            'Detach volume from server failed!')
