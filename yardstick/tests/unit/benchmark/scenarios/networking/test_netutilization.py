#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for
# yardstick.benchmark.scenarios.networking.netutilization.NetUtilization

from __future__ import absolute_import
import mock
import unittest
import os

from yardstick.benchmark.scenarios.networking import netutilization


@mock.patch('yardstick.benchmark.scenarios.networking.netutilization.ssh')
class NetUtilizationTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'cirros',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_setup_success(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }
        args = {'options': options}

        n = netutilization.NetUtilization(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        n.setup()
        self.assertIsNotNone(n.client)
        self.assertTrue(n.setup_done)

    def test_execute_command_success(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }
        args = {'options': options}

        n = netutilization.NetUtilization(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        n.setup()

        expected_result = 'abcdefg'
        mock_ssh.SSH.from_node().execute.return_value = (0, expected_result, '')
        result = n._execute_command("foo")
        self.assertEqual(result, expected_result)

    def test_execute_command_failed(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }
        args = {'options': options}

        n = netutilization.NetUtilization(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        n.setup()

        mock_ssh.SSH.from_node().execute.return_value = (127, '', 'abcdefg')
        self.assertRaises(RuntimeError, n._execute_command,
                          "failed")

    def test_get_network_utilization_success(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }
        args = {'options': options}

        n = netutilization.NetUtilization(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        n.setup()

        mpstat_output = self._read_file("netutilization_sample_output1.txt")
        mock_ssh.SSH.from_node().execute.return_value = (0, mpstat_output, '')
        result = n._get_network_utilization()

        expected_result = \
            {"network_utilization_maximun": {
                "lo": {"rxcmp/s": "0.00",
                       "%ifutil": "0.00",
                       "txcmp/s": "0.00",
                       "txkB/s": "0.00",
                       "rxkB/s": "0.00",
                       "rxpck/s": "0.00",
                       "txpck/s": "0.00",
                       "rxmcst/s": "0.00"},
                "eth0": {"rxcmp/s": "0.00",
                         "%ifutil": "0.00",
                         "txcmp/s": "0.00",
                         "txkB/s": "0.00",
                         "rxkB/s": "0.00",
                         "rxpck/s": "0.00",
                         "txpck/s": "0.00",
                         "rxmcst/s": "0.00"}},
             "network_utilization_average": {
                "lo": {"rxcmp/s": "0.00",
                       "%ifutil": "0.00",
                       "txcmp/s": "0.00",
                       "txkB/s": "0.00",
                       "rxkB/s": "0.00",
                       "rxpck/s": "0.00",
                       "txpck/s": "0.00",
                       "rxmcst/s": "0.00"},
                "eth0": {"rxcmp/s": "0.00",
                         "%ifutil": "0.00",
                         "txcmp/s": "0.00",
                         "txkB/s": "0.00",
                         "rxkB/s": "0.00",
                         "rxpck/s": "0.00",
                         "txpck/s": "0.00",
                         "rxmcst/s": "0.00"}},
             "network_utilization_minimum": {
                "lo": {"rxcmp/s": "0.00",
                       "%ifutil": "0.00",
                       "txcmp/s": "0.00",
                       "txkB/s": "0.00",
                       "rxkB/s": "0.00",
                       "rxpck/s": "0.00",
                       "txpck/s": "0.00",
                       "rxmcst/s": "0.00"},
                "eth0": {"rxcmp/s": "0.00",
                         "%ifutil": "0.00",
                         "txcmp/s": "0.00",
                         "txkB/s": "0.00",
                         "rxkB/s": "0.00",
                         "rxpck/s": "0.00",
                         "txpck/s": "0.00",
                         "rxmcst/s": "0.00"}}}

        self.assertDictEqual(result, expected_result)

    def test_get_network_utilization_2_success(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 2
        }
        args = {'options': options}

        n = netutilization.NetUtilization(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        n.setup()

        mpstat_output = self._read_file("netutilization_sample_output2.txt")
        mock_ssh.SSH.from_node().execute.return_value = (0, mpstat_output, '')
        result = n._get_network_utilization()

        expected_result = \
            {"network_utilization_maximun": {
                "lo": {"rxcmp/s": "0.00",
                       "%ifutil": "0.00",
                       "txcmp/s": "0.00",
                       "txkB/s": "0.00",
                       "rxkB/s": "0.00",
                       "rxpck/s": "0.00",
                       "txpck/s": "0.00",
                       "rxmcst/s": "0.00"},
                "eth0": {"rxcmp/s": "0.00",
                         "%ifutil": "0.00",
                         "txcmp/s": "0.00",
                         "txkB/s": "0.00",
                         "rxkB/s": "0.00",
                         "rxpck/s": "0.00",
                         "txpck/s": "0.00",
                         "rxmcst/s": "0.00"}},
             "network_utilization_average": {
                "lo": {"rxcmp/s": "0.00",
                       "%ifutil": "0.00",
                       "txcmp/s": "0.00",
                       "txkB/s": "0.00",
                       "rxkB/s": "0.00",
                       "rxpck/s": "0.00",
                       "txpck/s": "0.00",
                       "rxmcst/s": "0.00"},
                "eth0": {"rxcmp/s": "0.00",
                         "%ifutil": "0.00",
                         "txcmp/s": "0.00",
                         "txkB/s": "0.00",
                         "rxkB/s": "0.00",
                         "rxpck/s": "0.00",
                         "txpck/s": "0.00",
                         "rxmcst/s": "0.00"}},
             "network_utilization_minimum": {
                "lo": {"rxcmp/s": "0.00",
                       "%ifutil": "0.00",
                       "txcmp/s": "0.00",
                       "txkB/s": "0.00",
                       "rxkB/s": "0.00",
                       "rxpck/s": "0.00",
                       "txpck/s": "0.00",
                       "rxmcst/s": "0.00"},
                "eth0": {"rxcmp/s": "0.00",
                         "%ifutil": "0.00",
                         "txcmp/s": "0.00",
                         "txkB/s": "0.00",
                         "rxkB/s": "0.00",
                         "rxpck/s": "0.00",
                         "txpck/s": "0.00",
                         "rxmcst/s": "0.00"}}}

        self.assertDictEqual(result, expected_result)

    def _read_file(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output
