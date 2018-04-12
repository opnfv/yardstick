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

from yardstick.common import openstack_utils
from yardstick.common import exceptions
from yardstick.benchmark.scenarios.lib import delete_image


class DeleteImageTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_delete_image = mock.patch.object(
            openstack_utils, 'delete_image')
        self.mock_delete_image = (
            self._mock_delete_image.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(delete_image, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'image_name_or_id': 'yardstick_image'}}
        self.result = {}

        self.delimg_obj = delete_image.DeleteImage(self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_delete_image.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_delete_image.return_value = True
        self.assertIsNone(self.delimg_obj.run(self.result))
        self.assertEqual({'delete_image': 1}, self.result)
        self.mock_log.info.assert_called_once_with('Delete image successful!')

    def test_run_fail(self):
        self.mock_delete_image.return_value = False
        with self.assertRaises(exceptions.ScenarioDeleteImageError):
            self.delimg_obj.run(self.result)
        self.assertEqual({'delete_image': 0}, self.result)
        self.mock_log.error.assert_called_once_with('Delete image failed!')
