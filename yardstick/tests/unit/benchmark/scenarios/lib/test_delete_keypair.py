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
from yardstick.benchmark.scenarios.lib import delete_keypair


class DeleteKeypairTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_delete_keypair = mock.patch.object(
            openstack_utils, 'delete_keypair')
        self.mock_delete_keypair = self._mock_delete_keypair.start()
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(delete_keypair, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'key_name': 'yardstick_key'}}
        self.result = {}
        self.delkey_obj = delete_keypair.DeleteKeypair(self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_delete_keypair.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_delete_keypair.return_value = True
        self.assertIsNone(self.delkey_obj.run(self.result))
        self.assertEqual({'delete_keypair': 1}, self.result)
        self.mock_log.info.assert_called_once_with(
            'Delete keypair successful!')

    def test_run_fail(self):
        self.mock_delete_keypair.return_value = False
        with self.assertRaises(exceptions.ScenarioDeleteKeypairError):
            self.delkey_obj.run(self.result)
        self.assertEqual({'delete_keypair': 0}, self.result)
        self.mock_log.error.assert_called_once_with("Delete keypair failed!")
