#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.netperf.Netperf

import mock
import unittest
import os
import json

from yardstick.benchmark.scenarios.networking import netperf


@mock.patch('yardstick.benchmark.scenarios.networking.netperf.ssh')
class NetperfTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': '172.16.0.137',
            'target': '172.16.0.138',
            'user': 'cirros',
            'key_filename': "mykey.key"
        }

    def test_netperf_successful_setup(self, mock_ssh):

        p = netperf.Netperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')

        p.setup()
        self.assertIsNotNone(p.server)
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_netperf_successful_no_sla(self, mock_ssh):

        p = netperf.Netperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {'options': options}
        result = {}

        sample_output = self._read_sample_output()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        expected_result = json.loads(sample_output)
        p.run(args, result)
        self.assertEqual(result, expected_result)

    def test_netperf_successful_sla(self, mock_ssh):

        p = netperf.Netperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {
            'options': options,
            'sla': {'mean_latency': 100}
        }
        result = {}

        sample_output = self._read_sample_output()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        expected_result = json.loads(sample_output)
        p.run(args, result)
        self.assertEqual(result, expected_result)

    def test_netperf_unsuccessful_sla(self, mock_ssh):

        p = netperf.Netperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {
            'options': options,
            'sla': {'mean_latency': 5}
        }
        result = {}

        sample_output = self._read_sample_output()
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, args, result)

    def test_netperf_unsuccessful_script_error(self, mock_ssh):

        p = netperf.Netperf(self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')
        p.host = mock_ssh.SSH()

        options = {}
        args = {'options': options}
        result = {}

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, args, result)

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
