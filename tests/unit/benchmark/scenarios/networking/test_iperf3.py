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

import mock
import unittest
import os
import json

from yardstick.benchmark.scenarios.networking import iperf3


@mock.patch('yardstick.benchmark.scenarios.networking.iperf3.ssh')
class IperfTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': '172.16.0.137',
            'target': '172.16.0.138',
            'user': 'cirros',
            'key_filename': "mykey.key"
        }

    def test_iperf_successful_setup(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')

        p.setup()
        self.assertIsNotNone(p.target)
        self.assertIsNotNone(p.host)
        mock_ssh.SSH().execute.assert_called_with("iperf3 -s -D")

    def test_iperf_unsuccessful_setup(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.setup)

    def test_iperf_successful_teardown(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()
        p.target = mock_ssh.SSH()

        p.teardown()
        self.assertTrue(mock_ssh.SSH().close.called)
        mock_ssh.SSH().execute.assert_called_with("pkill iperf3")

    def test_iperf_successful_no_sla(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {'options': options}

        sample_output = self._read_sample_output()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        expected_result = json.loads(sample_output)
        result = p.run(args)
        self.assertEqual(result, expected_result)

    def test_iperf_successful_sla(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {
            'options': options,
            'sla': {'bytes_per_second': 15000000}
        }

        sample_output = self._read_sample_output()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        expected_result = json.loads(sample_output)
        result = p.run(args)
        self.assertEqual(result, expected_result)

    def test_iperf_unsuccessful_sla(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {
            'options': options,
            'sla': {'bytes_per_second': 25000000}
        }

        sample_output = self._read_sample_output()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, args)

    def test_iperf_successful_sla_jitter(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {"udp":"udp","bandwidth":"20m"}
        args = {
            'options': options,
            'sla': {'jitter': 10}
        }

        sample_output = self._read_sample_output_udp()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        expected_result = json.loads(sample_output)
        result = p.run(args)
        self.assertEqual(result, expected_result)

    def test_iperf_unsuccessful_sla_jitter(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {"udp":"udp","bandwidth":"20m"}
        args = {
            'options': options,
            'sla': {'jitter': 0.0001}
        }

        sample_output = self._read_sample_output_udp()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, args)

    def test_iperf_unsuccessful_script_error(self, mock_ssh):

        p = iperf3.Iperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {'options': options}

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, args)

    def _read_sample_output(self):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, 'iperf3_sample_output.json')
        with open(output) as f:
            sample_output = f.read()
        return sample_output

    def _read_sample_output_udp(self):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, 'iperf3_sample_output_udp.json')
        with open(output) as f:
            sample_output = f.read()
        return sample_output

def main():
    unittest.main()

if __name__ == '__main__':
    main()
