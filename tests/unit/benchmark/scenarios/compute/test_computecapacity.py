#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.computecapacity.ComputeCapacity

import mock
import unittest
import os
import json

from yardstick.benchmark.scenarios.compute import computecapacity


@mock.patch('yardstick.benchmark.scenarios.compute.computecapacity.ssh')
class ComputeCapacityTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'nodes': {
                'host1': {
                    'ip': '172.16.0.137',
                    'user': 'cirros',
                    'key_filename': "mykey.key",
                    'password': "root"
                },
            }
        }

        self.result = {}

    def test_capacity_successful_setup(self, mock_ssh):
        c = computecapacity.ComputeCapacity({}, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, '', '')

        c.setup()
        self.assertIsNotNone(c.client)
        self.assertTrue(c.setup_done)

    def test_capacity_successful(self, mock_ssh):
        c = computecapacity.ComputeCapacity({}, self.ctx)

        sample_output = '{"Cpu_number": "2", "Core_number": "24",\
 "Memory_size": "263753976 kB", "Thread_number": "48",\
 "Cache_size": "30720 KB"}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        c.run(self.result)
        expected_result = json.loads(sample_output)
        self.assertEqual(self.result, expected_result)

    def test_capacity_unsuccessful_script_error(self, mock_ssh):
        c = computecapacity.ComputeCapacity({}, self.ctx)

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, c.run, self.result)
