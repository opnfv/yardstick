#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.storage.bonnie.Bonnie

from __future__ import absolute_import

import unittest

import mock

from yardstick.common import utils
from yardstick.benchmark.scenarios.storage import bonnie


@mock.patch('yardstick.benchmark.scenarios.storage.bonnie.ssh')
@mock.patch('yardstick.benchmark.scenarios.storage.bonnie.subprocess')
class BonnieTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_bonnie_successful_setup(self, mock_ssh):

        options = {
            "file_size": "1024",
            "ram_size": "512",
            "test_dir": "/tmp",
            "concurrency": "1",
            "test_user": "root"
        }
        args = {"options": options}
        b = bonnie.Bonnie(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        b.setup()
        self.assertIsNotNone(b.client)
        self.assertTrue(b.setup_done, True)

    def test_bonnie_successful_run(self, mock_ssh, mock_subprocess):

        options = {
            "file_size": "1024",
            "ram_size": "512",
            "test_dir": "/tmp",
            "concurrency": "1",
            "test_user": "root"
        }
        args = {"options": options}
        b = bonnie.Bonnie(args, self.ctx)

        sample_output = '1.97,1.97,bonnie,1,1501658820,1G,,804,65,193281,14,108497,8,4576,99,\
                         192159,8,+++++,+++,16,,,,,+++++,+++,+++++,+++,+++++,+++,+++++,+++,\
                         +++++,+++,+++++,+++,20287us,441ms,329ms,2408us,2581us,1820us,101us,\
                         338us,425us,2185us,23us,149us\n'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        mock_subprocess.Popen.return_value = (0, 'unittest')
        b.run(self.result)
        expected_result = sample_output.split('\n')[-2]
        self.assertEqual(self.result['raw_data'], expected_result)

    def test_bonnie_unsuccessful_script_error(self, mock_ssh):
        options = {
            "file_size": "1024",
            "ram_size": "512",
            "test_dir": "/tmp",
            "concurrency": "1",
            "test_user": "root"
        }
        args = {"options": options}
        b = bonnie.Bonnie(args, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, b.run, self.result)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
