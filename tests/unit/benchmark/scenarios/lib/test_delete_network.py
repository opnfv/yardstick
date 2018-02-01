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

import yardstick.common.openstack_utils as op_utils
from yardstick.benchmark.scenarios.lib import delete_network


class DeleteNetworkTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_delete_neutron_net = mock.patch.object(
            op_utils, 'delete_neutron_net')
        self.mock_delete_neutron_net = self._mock_delete_neutron_net.start()
        self._mock_get_shade_client = mock.patch.object(
            op_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(delete_network, 'LOG')
        self.mock_log = self._mock_log.start()
        _uuid = uuidutils.generate_uuid()
        self.args = {'options': {'network_id': _uuid}}
        self._del_obj = delete_network.DeleteNetwork(self.args, mock.ANY)

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_delete_neutron_net.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        self.mock_delete_neutron_net.return_value = True
        output = self._del_obj.run({})
        self.assertEqual(True, output)
        self.assertTrue(self.mock_log.info.called)

    def test_run_fail(self):
        self.mock_delete_neutron_net.return_value = False
        output = self._del_obj.run({})
        self.assertEqual(False, output)
        self.assertTrue(self.mock_log.error.called)