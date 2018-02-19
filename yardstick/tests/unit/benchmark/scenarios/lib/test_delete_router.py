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
from yardstick.benchmark.scenarios.lib import delete_router


class DeleteRouterTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_delete_neutron_router = mock.patch.object(
            openstack_utils, 'delete_neutron_router')
        self.mock_delete_neutron_router = (
            self._mock_delete_neutron_router.start())
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(delete_router, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'router_id': uuidutils.generate_uuid()}}
        self.result = {"delete_router": 0}

        self._del_obj = delete_router.DeleteRouter(self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_delete_neutron_router.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_delete_neutron_router.return_value = True
        self.assertIsNone(self._del_obj.run(self.result))
        self.assertEqual({"delete_router": 1}, self.result)
        self.mock_log.info.assert_called_once_with("Delete router successful!")

    def test_run_fail(self):
        self.mock_delete_neutron_router.return_value = False
        with self.assertRaises(exceptions.ScenarioDeleteRouterError):
            self._del_obj.run(self.result)
        self.assertEqual({"delete_router": 0}, self.result)
        self.mock_log.error.assert_called_once_with("Delete router failed!")
>>>>>>> Replace neutron router deletion with shade.
