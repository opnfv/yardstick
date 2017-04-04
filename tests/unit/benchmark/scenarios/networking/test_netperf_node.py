#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for
# yardstick.benchmark.scenarios.networking.netperf_node.NetperfNode

from __future__ import absolute_import

import os
import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.networking import netperf_node


@mock.patch('yardstick.benchmark.scenarios.networking.netperf_node.ssh')
class NetperfNodeTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '192.168.10.10',
                'user': 'root',
                'password': 'root'
            },
            'target': {
                'ip': '192.168.10.11',
                'user': 'root',
                'password': 'root'
            }
        }

    def test_netperf_node_successful_setup(self, mock_ssh):

        p = netperf_node.NetperfNode({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p.setup()
        self.assertIsNotNone(p.server)
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_netperf_node_successful_no_sla(self, mock_ssh):

        options = {}
        args = {'options': options}
        result = {}

        p = netperf_node.NetperfNode(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output()
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        expected_result = jsonutils.loads(sample_output)
        p.run(result)
        self.assertEqual(result, expected_result)

    def test_netperf_node_successful_sla(self, mock_ssh):

        options = {}
        args = {
            'options': options,
            'sla': {'mean_latency': 100}
        }
        result = {}

        p = netperf_node.NetperfNode(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output()
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        expected_result = jsonutils.loads(sample_output)
        p.run(result)
        self.assertEqual(result, expected_result)

    def test_netperf_node_unsuccessful_sla(self, mock_ssh):

        options = {}
        args = {
            'options': options,
            'sla': {'mean_latency': 5}
        }
        result = {}

        p = netperf_node.NetperfNode(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output()
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_netperf_node_unsuccessful_script_error(self, mock_ssh):

        options = {}
        args = {'options': options}
        result = {}

        p = netperf_node.NetperfNode(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)

    def _read_sample_output(self):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, 'netperf_sample_output.json')
        with open(output) as f:
            sample_output = f.read()
        return sample_output


def main():
    unittest.main()

if __name__ == '__main__':
    main()
