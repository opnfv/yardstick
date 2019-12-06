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
import os
from yardstick.benchmark.scenarios.energy import energy


class EnergyTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'target': {
                'ip': '172.16.0.137',
                'user': 'root',
                'password': 'passw0rd',
                'redfish_ip': '10.229.17.105',
                'redfish_user': 'USERID',
                'redfish_pwd': "PASSW0RD",
            }
        }
        self.result = {}

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_setup_response_success(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        p.setup()
        self.assertTrue(p.get_response)
        self.assertTrue(p.setup_done)

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_setup_response_failed(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 404
        p.setup()
        self.assertFalse(p.get_response)
        self.assertTrue(p.setup_done)

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_load_chassis_list_success(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        expect_result = self._read_file("energy_sample_chassis_output.txt")
        expect_result = str(expect_result)
        expect_result = expect_result.replace("'", '"')
        mock_send_request.return_value.status_code = 200
        mock_send_request.return_value.text = expect_result
        self.result = p.load_chassis_list()
        self.assertEqual(self.result, ["/redfish/v1/Chassis/1"])

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_load_chassis_response_fail(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 404
        self.result = p.load_chassis_list()
        self.assertEqual(self.result, [])

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_load_chassis_wrongtype_response(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        expect_result = {}
        mock_send_request.return_value.text = expect_result
        self.result = p.load_chassis_list()
        self.assertEqual(self.result, [])

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_load_chassis_inporper_key(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        expect_result = '{"some_key": "some_value"}'
        mock_send_request.return_value.text = expect_result
        self.result = p.load_chassis_list()
        self.assertEqual(self.result, [])

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_energy_getpower_success(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        expect_result = self._read_file("energy_sample_power_metrics.txt")
        expect_result = str(expect_result)
        expect_result = expect_result.replace("'", '"')
        mock_send_request.return_value.status_code = 200
        mock_send_request.return_value.text = expect_result
        self.result = p.get_power("/redfish/v1/Chassis/1")
        self.assertEqual(self.result, 344)

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_energy_getpower_response_fail(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 404
        self.result = p.get_power("/redfish/v1/Chassis/1")
        self.assertEqual(self.result, -1)

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_energy_getpower_wrongtype_response(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        expect_result = {}
        mock_send_request.return_value.text = expect_result
        self.result = p.get_power("/redfish/v1/Chassis/1")
        self.assertEqual(self.result, -1)

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_energy_getpower_inproper_key(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        expect_result = '{"some_key": "some_value"}'
        mock_send_request.return_value.text = expect_result
        self.result = p.get_power("/redfish/v1/Chassis/1")
        self.assertEqual(self.result, -1)

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_run_success(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        chassis_list = mock.Mock(return_value=["/redfish/v1/Chassis/1"])
        p.load_chassis_list = chassis_list
        power = mock.Mock(return_value=344)
        p.get_power = power
        p.run(self.result)
        self.assertEqual(self.result, {"power": 344})

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_run_no_response(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 404
        chassis_list = mock.Mock(return_value=["/redfish/v1/Chassis/1"])
        p.load_chassis_list = chassis_list
        p.run(self.result)
        self.assertEqual(self.result, {"power": -1})

    @mock.patch('yardstick.benchmark.scenarios.'
                'energy.energy.Energy._send_request')
    def test_run_wrong_chassis(self, mock_send_request):
        args = {}
        p = energy.Energy(args, self.ctx)
        mock_send_request.return_value.status_code = 200
        chassis_list = mock.Mock(return_value=[])
        p.load_chassis_list = chassis_list
        p.run(self.result)
        self.assertEqual(self.result, {"power": -1})

    def _read_file(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output
