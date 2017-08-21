#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.lmbench.Lmbench

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.compute import lmbench


@mock.patch('yardstick.benchmark.scenarios.compute.lmbench.ssh')
class LmbenchTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'cirros',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_successful_setup(self, mock_ssh):

        l = lmbench.Lmbench({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        l.setup()
        self.assertIsNotNone(l.client)
        self.assertTrue(l.setup_done)

    def test_unsuccessful_unknown_type_run(self, mock_ssh):

        options = {
            "test_type": "foo"
        }
        args = {'options': options}

        l = lmbench.Lmbench(args, self.ctx)

        self.assertRaises(RuntimeError, l.run, self.result)

    def test_successful_latency_run_no_sla(self, mock_ssh):

        options = {
            "test_type": "latency",
            "stride": 64,
            "stop_size": 16
        }
        args = {'options': options}
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = '[{"latency": 4.944, "size": 0.00049}]'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        l.run(self.result)
        expected_result = {"latencies0.latency": 4.944, "latencies0.size": 0.00049}
        self.assertEqual(self.result, expected_result)

    def test_successful_bandwidth_run_no_sla(self, mock_ssh):

        options = {
            "test_type": "bandwidth",
            "size": 500,
            "benchmark": "rd",
            "warmup": 0
        }
        args = {"options": options}
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = '{"size(MB)": 0.262144, "bandwidth(MBps)": 11025.5}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        l.run(self.result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(self.result, expected_result)

    def test_successful_latency_run_sla(self, mock_ssh):

        options = {
            "test_type": "latency",
            "stride": 64,
            "stop_size": 16
        }
        args = {
            "options": options,
            "sla": {"max_latency": 35}
        }
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = '[{"latency": 4.944, "size": 0.00049}]'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        l.run(self.result)
        expected_result = {"latencies0.latency": 4.944, "latencies0.size": 0.00049}
        self.assertEqual(self.result, expected_result)

    def test_successful_bandwidth_run_sla(self, mock_ssh):

        options = {
            "test_type": "bandwidth",
            "size": 500,
            "benchmark": "rd",
            "warmup": 0
        }
        args = {
            "options": options,
            "sla": {"min_bandwidth": 10000}
        }
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = '{"size(MB)": 0.262144, "bandwidth(MBps)": 11025.5}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        l.run(self.result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(self.result, expected_result)

    def test_unsuccessful_latency_run_sla(self, mock_ssh):

        options = {
            "test_type": "latency",
            "stride": 64,
            "stop_size": 16
        }
        args = {
            "options": options,
            "sla": {"max_latency": 35}
        }
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = '[{"latency": 37.5, "size": 0.00049}]'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, l.run, self.result)

    def test_unsuccessful_bandwidth_run_sla(self, mock_ssh):

        options = {
            "test_type": "bandwidth",
            "size": 500,
            "benchmark": "rd",
            "warmup": 0
        }
        args = {
            "options": options,
            "sla": {"min_bandwidth": 10000}
        }
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = '{"size(MB)": 0.262144, "bandwidth(MBps)": 9925.5}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, l.run, self.result)

    def test_successful_latency_for_cache_run_sla(self, mock_ssh):

        options = {
            "test_type": "latency_for_cache",
            "repetition": 1,
            "warmup": 0
        }
        args = {
            "options": options,
            "sla": {"max_latency": 35}
        }
        l = lmbench.Lmbench(args, self.ctx)

        sample_output = "{\"L1cache\": 1.6}"
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        l.run(self.result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(self.result, expected_result)

    def test_unsuccessful_script_error(self, mock_ssh):

        options = {"test_type": "bandwidth"}
        args = {"options": options}
        l = lmbench.Lmbench(args, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, l.run, self.result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
