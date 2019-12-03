##############################################################################
# Copyright (c) 2019 Lenovo Group Limited Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.energy.energy.Energy

from __future__ import absolute_import
import unittest
import mock
import json
import os
from yardstick.benchmark.scenarios.energy import energy
from yardstick.common import exceptions as y_exc


class EnergyTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'password': 'passw0rd'
            },
            'target': {
                'redfish_ip': '10.229.17.105',
                'redfish_user': 'USERID',
                'redfish_pwd': "PASSW0RD",
            }
        }

    @mock.patch('yardstick.benchmark.scenarios.energy.energy.ssh')
    def test_load_chassis_list(self, mock_ssh):
        args = {}
        result = {}
        p = energy.Energy(args, self.ctx)
        expect_result = self._read_file("energy_sample_chassis_output.txt")
        expect_result = str(expect_result)
        expect_result = expect_result.replace("'", '"')
        mock_ssh.SSH.from_node().execute.return_value = (0, expect_result, '')
        result = p.load_chassis_list()
        self.assertEqual(result, ["/redfish/v1/Chassis/1"])

    @mock.patch('yardstick.benchmark.scenarios.energy.energy.ssh')
    def test_energy_getpower(self, mock_ssh):
        args = {}
        result = {}
        p = energy.Energy(args, self.ctx)
        expect_result = self._read_file("energy_sample_power_metrics.txt")
        expect_result = str(expect_result)
        expect_result = expect_result.replace("'", '"')
        mock_ssh.SSH.from_node().execute.return_value = (0, expect_result, '')
        result = p.get_power("/redfish/v1/Chassis/1")
        self.assertEqual(result, 344)

    def _read_file(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output
