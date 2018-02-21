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

from yardstick.benchmark.scenarios.lib import delete_router_interface
from yardstick.common import openstack_utils
from yardstick.common import exceptions


class DeleteRouterInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_remove_router_interface = mock.patch.object(
            openstack_utils, 'remove_router_interface')
        self.mock_remove_router_interface = (
            self._mock_remove_router_interface.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(delete_router_interface, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'router': uuidutils.generate_uuid()}}
        self.result = {}
        self._delrout_obj = delete_router_interface.DeleteRouterInterface(
            self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_remove_router_interface.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_remove_router_interface.return_value = True
        self.assertIsNone(self._delrout_obj.run(self.result))
        self.assertEqual({"delete_router_interface": 1}, self.result)
        self.mock_log.info.assert_called_once_with(
            "Delete router interface successful!")

    def test_run_fail(self):
        self.mock_remove_router_interface.return_value = False
        with self.assertRaises(exceptions.ScenarioRemoveRouterIntError):
            self._delrout_obj.run(self.result)
        self.assertEqual({"delete_router_interface": 0}, self.result)
        self.mock_log.error.assert_called_once_with(
            "Delete router interface failed!")
