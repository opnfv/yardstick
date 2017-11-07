#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.memload.MEMLoad

from __future__ import absolute_import
import mock
import unittest
import os

from yardstick.benchmark.scenarios.compute import memload


@mock.patch('yardstick.benchmark.scenarios.compute.memload.ssh')
class MEMLoadTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_memload_successful_setup(self, mock_ssh):
        m = memload.MEMLoad({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        m.setup()
        self.assertIsNotNone(m.client)
        self.assertTrue(m.setup_done)

    def test_execute_command_success(self, mock_ssh):
        m = memload.MEMLoad({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        m.setup()

        expected_result = 'abcdefg'
        mock_ssh.SSH.from_node().execute.return_value = (0, expected_result, '')
        result = m._execute_command("foo")
        self.assertEqual(result, expected_result)

    def test_execute_command_failed(self, mock_ssh):
        m = memload.MEMLoad({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        m.setup()

        mock_ssh.SSH.from_node().execute.return_value = (127, '', 'Failed executing \
                                               command')
        self.assertRaises(RuntimeError, m._execute_command,
                          "cat /proc/meminfo")

    def test_get_mem_usage_successful(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }
        args = {"options": options}
        m = memload.MEMLoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        m.setup()

        output = self._read_file("memload_sample_output.txt")
        mock_ssh.SSH.from_node().execute.return_value = (0, output, '')
        result = m._get_mem_usage()
        expected_result = {
            "max": {
                'shared': 2844,
                'buff/cache': 853528,
                'total': 263753976,
                'free': 187016644,
                'used': 76737332
            },
            "average": {
                'shared': 2844,
                'buff/cache': 853528,
                'total': 263753976,
                'free': 187016644,
                'used': 76737332
            },
            "free": {
                "memory0": {
                    "used": "76737332",
                    "buff/cache": "853528",
                    "free": "187016644",
                    "shared": "2844",
                    "total": "263753976",
                    "available": "67252400"
                }
            }
        }

        self.assertEqual(result, expected_result)

    def _read_file(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output


def main():
    unittest.main()


if __name__ == '__main__':
    main()
