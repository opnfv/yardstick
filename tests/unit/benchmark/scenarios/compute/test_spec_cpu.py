#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.spec_cpu.SpecCPU

from __future__ import absolute_import

import unittest

import mock

from yardstick.common import utils
from yardstick.benchmark.scenarios.compute import spec_cpu


@mock.patch('yardstick.benchmark.scenarios.compute.spec_cpu.ssh')
class SpecCPUTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_spec_cpu_successful_setup(self, mock_ssh):

        options = {
            "SPECint_benchmark": "perlbench",
            "runspec_tune": "all",
            "output_format": "all",
            "runspec_iterations": "1",
            "runspec_tune": "base",
            "runspec_size": "test"
        }
        args = {"options": options}
        s = spec_cpu.SpecCPU(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        s.setup()
        self.assertIsNotNone(s.client)
        self.assertTrue(s.setup_done, True)

    def test_spec_cpu_successful__run_no_sla(self, mock_ssh):

        options = {
            "SPECint_benchmark": "perlbench",
            "runspec_tune": "all",
            "output_format": "all"
        }
        args = {"options": options}
        s = spec_cpu.SpecCPU(args, self.ctx)

        sample_output = ''
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        s.run(self.result)
        expected_result = {}
        self.assertEqual(self.result, expected_result)

    def test_ramspeed_unsuccessful_script_error(self, mock_ssh):
        options = {
            "benchmark_subset": "int"
        }
        args = {"options": options}
        s = spec_cpu.SpecCPU(args, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, s.run, self.result)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
