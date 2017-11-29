#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for
# yardstick.benchmark.scenarios.compute.computecapacity.ComputeCapacity

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.compute import computecapacity

SAMPLE_OUTPUT = '{"Cpu_number": "2", "Core_number": "24",\
 "Memory_size": "263753976 kB", "Thread_number": "48",\
 "Cache_size": "30720 KB", "HT_Open": "0"}'


@mock.patch('yardstick.benchmark.scenarios.compute.computecapacity.ssh')
class ComputeCapacityTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'nodes': {
                'host': {
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
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        c.setup()
        self.assertIsNotNone(c.client)
        self.assertTrue(c.setup_done)

    def test_capacity_successful(self, mock_ssh):
        c = computecapacity.ComputeCapacity({}, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (0, SAMPLE_OUTPUT, '')
        c.run(self.result)
        expected_result = jsonutils.loads(SAMPLE_OUTPUT)
        self.assertEqual(self.result, expected_result)

    def test_capacity_unsuccessful_script_error(self, mock_ssh):
        c = computecapacity.ComputeCapacity({}, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, c.run, self.result)
