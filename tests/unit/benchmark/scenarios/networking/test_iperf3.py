#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.iperf3.Iperf

from __future__ import absolute_import

import os
import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.common import utils
from yardstick.benchmark.scenarios.networking import iperf3


@mock.patch('yardstick.benchmark.scenarios.networking.iperf3.ssh')
class IperfTestCase(unittest.TestCase):
    output_name_tcp = 'iperf3_sample_output.json'
    output_name_udp = 'iperf3_sample_output_udp.json'

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': 'mykey.key'
            },
            'target': {
                'ip': '172.16.0.138',
                'user': 'root',
                'key_filename': 'mykey.key',
                'ipaddr': '172.16.0.138',
            }
        }

    def test_iperf_successful_setup(self, mock_ssh):

        p = iperf3.Iperf({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        p.setup()
        self.assertIsNotNone(p.target)
        self.assertIsNotNone(p.host)
        mock_ssh.SSH.from_node().execute.assert_called_with("iperf3 -s -D")

    def test_iperf_unsuccessful_setup(self, mock_ssh):

        p = iperf3.Iperf({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.setup)

    def test_iperf_successful_teardown(self, mock_ssh):

        p = iperf3.Iperf({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()
        p.target = mock_ssh.SSH.from_node()

        p.teardown()
        self.assertTrue(mock_ssh.SSH.from_node().close.called)
        mock_ssh.SSH.from_node().execute.assert_called_with("pkill iperf3")

    def test_iperf_successful_no_sla(self, mock_ssh):

        options = {}
        args = {'options': options}
        result = {}

        p = iperf3.Iperf(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.output_name_tcp)
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        p.run(result)
        self.assertEqual(result, expected_result)

    def test_iperf_successful_sla(self, mock_ssh):

        options = {}
        args = {
            'options': options,
            'sla': {'bytes_per_second': 15000000}
        }
        result = {}

        p = iperf3.Iperf(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.output_name_tcp)
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        p.run(result)
        self.assertEqual(result, expected_result)

    def test_iperf_unsuccessful_sla(self, mock_ssh):

        options = {}
        args = {
            'options': options,
            'sla': {'bytes_per_second': 25000000}
        }
        result = {}

        p = iperf3.Iperf(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.output_name_tcp)
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_iperf_successful_sla_jitter(self, mock_ssh):
        options = {"udp": "udp", "bandwidth": "20m"}
        args = {
            'options': options,
            'sla': {'jitter': 10}
        }
        result = {}

        p = iperf3.Iperf(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.output_name_udp)
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        p.run(result)
        self.assertEqual(result, expected_result)

    def test_iperf_unsuccessful_sla_jitter(self, mock_ssh):
        options = {"udp": "udp", "bandwidth": "20m"}
        args = {
            'options': options,
            'sla': {'jitter': 0.0001}
        }
        result = {}

        p = iperf3.Iperf(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.output_name_udp)
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_iperf_unsuccessful_script_error(self, mock_ssh):

        options = {}
        args = {'options': options}
        result = {}

        p = iperf3.Iperf(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)

    def _read_sample_output(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output


def main():
    unittest.main()

if __name__ == '__main__':
    main()
