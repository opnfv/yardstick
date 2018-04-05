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
from yardstick.benchmark.scenarios.lib import get_flavor


class GetFlavorTestCase(unittest.TestCase):

    def setUp(self):

        self._mock_get_flavor = mock.patch.object(
            openstack_utils, 'get_flavor')
        self.mock_get_flavor = self._mock_get_flavor.start()
        self._mock_get_shade_client = mock.patch.object(
            openstack_utils, 'get_shade_client')
        self.mock_get_shade_client = self._mock_get_shade_client.start()
        self._mock_log = mock.patch.object(get_flavor, 'LOG')
        self.mock_log = self._mock_log.start()
        self.args = {'options': {'flavor_name_or_id': 'yardstick_flavor'}}
        self.result = {}

        self.getflavor_obj = get_flavor.GetFlavor(self.args, mock.ANY)
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_get_flavor.stop()
        self._mock_get_shade_client.stop()
        self._mock_log.stop()

    def test_run(self):
        _uuid = uuidutils.generate_uuid()
        self.getflavor_obj.scenario_cfg = {'output': 'flavor'}
        self.mock_get_flavor.return_value = {
            'flavor': {'name': 'flavor-name', 'id': _uuid}}
        output = self.getflavor_obj.run(self.result)
        self.assertDictEqual({'get_flavor': 1}, self.result)
        self.assertDictEqual({'flavor': {'name': 'flavor-name', 'id': _uuid}},
                             output)
        self.mock_log.info.asset_called_once_with('Get flavor successful!')

    def test_run_fail(self):
        self.mock_get_flavor.return_value = None
        with self.assertRaises(exceptions.ScenarioGetFlavorError):
            self.getflavor_obj.run(self.result)
        self.assertDictEqual({'get_flavor': 0}, self.result)
        self.mock_log.error.assert_called_once_with('Get flavor failed!')
