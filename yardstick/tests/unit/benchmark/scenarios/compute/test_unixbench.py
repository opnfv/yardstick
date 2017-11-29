#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.unixbench.Unixbench

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.compute import unixbench


@mock.patch('yardstick.benchmark.scenarios.compute.unixbench.ssh')
class UnixbenchTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "192.168.50.28",
                "user": "root",
                "key_filename": "mykey.key"
            }
        }

    def test_unixbench_successful_setup(self, mock_ssh):

        u = unixbench.Unixbench({}, self.ctx)
        u.setup()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.assertIsNotNone(u.client)
        self.assertEqual(u.setup_done, True)

    def test_unixbench_successful_no_sla(self, mock_ssh):

        options = {
            "test_type": 'dhry2reg',
            "run_mode": 'verbose'
        }
        args = {
            "options": options,
        }
        u = unixbench.Unixbench(args, self.ctx)
        result = {}

        u.server = mock_ssh.SSH.from_node()

        sample_output = '{"Score":"4425.4"}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        u.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_unixbench_successful_in_quiet_mode(self, mock_ssh):

        options = {
            "test_type": 'dhry2reg',
            "run_mode": 'quiet',
            "copies": 1
        }
        args = {
            "options": options,
        }
        u = unixbench.Unixbench(args, self.ctx)
        result = {}

        u.server = mock_ssh.SSH.from_node()

        sample_output = '{"Score":"4425.4"}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        u.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_unixbench_successful_sla(self, mock_ssh):

        options = {
            "test_type": 'dhry2reg',
            "run_mode": 'verbose'
        }
        sla = {
            "single_score": '100',
            "parallel_score": '500'
        }
        args = {
            "options": options,
            "sla": sla
        }
        u = unixbench.Unixbench(args, self.ctx)
        result = {}

        u.server = mock_ssh.SSH.from_node()

        sample_output = '{"signle_score":"2251.7","parallel_score":"4395.9"}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        u.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_unixbench_unsuccessful_sla_single_score(self, mock_ssh):

        args = {
            "options": {},
            "sla": {"single_score": "500"}
        }
        u = unixbench.Unixbench(args, self.ctx)
        result = {}

        u.server = mock_ssh.SSH.from_node()
        sample_output = '{"single_score":"200.7","parallel_score":"4395.9"}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, u.run, result)

    def test_unixbench_unsuccessful_sla_parallel_score(self, mock_ssh):

        args = {
            "options": {},
            "sla": {"parallel_score": "4000"}
        }
        u = unixbench.Unixbench(args, self.ctx)
        result = {}

        u.server = mock_ssh.SSH.from_node()
        sample_output = '{"signle_score":"2251.7","parallel_score":"3395.9"}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, u.run, result)

    def test_unixbench_unsuccessful_script_error(self, mock_ssh):

        options = {
            "test_type": 'dhry2reg',
            "run_mode": 'verbose'
        }
        sla = {
            "single_score": '100',
            "parallel_score": '500'
        }
        args = {
            "options": options,
            "sla": sla
        }
        u = unixbench.Unixbench(args, self.ctx)
        result = {}

        u.server = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, u.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
