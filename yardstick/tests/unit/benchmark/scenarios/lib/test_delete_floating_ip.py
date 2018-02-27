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
from yardstick.benchmark.scenarios.lib import delete_floating_ip


class DeleteFloatingIpTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_delete_floating_ip = mock.patch.object(
            openstack_utils, 'delete_floating_ip')
        self.mock_delete_floating_ip = self._mock_delete_floating_ip.start()
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(delete_floating_ip, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'floating_ip_id': uuidutils.generate_uuid()}}
        self.result = {}

        self._del_obj = delete_floating_ip.DeleteFloatingIp(
            self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_delete_floating_ip.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_delete_floating_ip.return_value = True
        self.assertIsNone(self._del_obj.run(self.result))
        self.assertEqual({"delete_floating_ip": 1}, self.result)
        self.mock_log.info.assert_called_once_with(
            "Delete floating ip successful!")

    def test_run_fail(self):
        self.mock_delete_floating_ip.return_value = False
        with self.assertRaises(exceptions.ScenarioDeleteFloatingIPError):
            self._del_obj.run(self.result)
        self.assertEqual({"delete_floating_ip": 0}, self.result)
        self.mock_log.error.assert_called_once_with(
            "Delete floating ip failed!")
