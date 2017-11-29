#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.cachestat.CACHEstat

from __future__ import absolute_import
import mock
import unittest
import os

from yardstick.benchmark.scenarios.compute import cachestat


@mock.patch('yardstick.benchmark.scenarios.compute.cachestat.ssh')
class CACHEstatTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_cachestat_successful_setup(self, mock_ssh):
        c = cachestat.CACHEstat({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        c.setup()
        self.assertIsNotNone(c.client)
        self.assertTrue(c.setup_done)

    def test_execute_command_success(self, mock_ssh):
        c = cachestat.CACHEstat({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        expected_result = 'abcdefg'
        mock_ssh.SSH.from_node().execute.return_value = (0, expected_result, '')
        result = c._execute_command("foo")
        self.assertEqual(result, expected_result)

    def test_execute_command_failed(self, mock_ssh):
        c = cachestat.CACHEstat({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        mock_ssh.SSH.from_node().execute.return_value = (127, '', 'Failed executing \
            command')
        self.assertRaises(RuntimeError, c._execute_command,
                          "cat /proc/meminfo")

    def test_get_cache_usage_successful(self, mock_ssh):
        options = {
            "interval": 1,
        }
        args = {"options": options}
        c = cachestat.CACHEstat(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        output = self._read_file("cachestat_sample_output.txt")
        mock_ssh.SSH.from_node().execute.return_value = (0, output, '')
        result = c._get_cache_usage()
        expected_result = {"cachestat": {"cache0": {"HITS": "6462",
                                                    "DIRTIES": "29",
                                                    "RATIO": "100.0%",
                                                    "MISSES": "0",
                                                    "BUFFERS_MB": "1157",
                                                    "CACHE_MB": "66782"}},
                           "average": {"HITS": 6462, "DIRTIES": 29,
                                       "RATIO": "100.0%",
                                       "MISSES": 0, "BUFFERS_MB": 1157,
                                       "CACHE_MB": 66782},
                           "max": {"HITS": 6462,
                                   "DIRTIES": 29, "RATIO": 100.0, "MISSES": 0,
                                   "BUFFERS_MB": 1157, "CACHE_MB": 66782}}

        self.assertEqual(result, expected_result)

    def _read_file(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output
