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

    @mock.patch('yardstick.benchmark.scenarios.storage.bonnie.ssh')
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

    @mock.patch('yardstick.benchmark.scenarios.storage.bonnie.ssh')
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
