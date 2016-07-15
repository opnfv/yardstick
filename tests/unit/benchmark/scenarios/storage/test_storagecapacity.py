#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.storage.storagecapacity.StorageCapacity

import mock
import unittest
import os
import json

from yardstick.benchmark.scenarios.storage import storagecapacity

DISK_SIZE_SAMPLE_OUTPUT = '{"Numberf of devides": "2", "Total disk size": "1024000000 bytes"}'
BLOCK_SIZE_SAMPLE_OUTPUT = '{"/dev/sda": 1024, "/dev/sdb": 4096}'
DISK_UTIL_SAMPLE_OUTPUT = '{"vda": {"avg_util": 4.962, "max_util": 24.81, "min_util": 0.0}, \
                            "scd0": {"avg_util": 0.046, "max_util": 0.23, "min_util": 0.0}}'

@mock.patch('yardstick.benchmark.scenarios.storage.storagecapacity.ssh')
class StorageCapacityTestCase(unittest.TestCase):

    def setUp(self):
        self.scn = {
               "options": {
                   'test_type': 'disk_size'
               }
        }
        self.ctx = {
                "host": {
                    'ip': '172.16.0.137',
                    'user': 'cirros',
                    'password': "root"
                }
        }
        self.result = {}

    def test_capacity_successful_setup(self, mock_ssh):
        c = storagecapacity.StorageCapacity(self.scn, self.ctx)

        mock_ssh.SSH().execute.return_value = (0, '', '')
        c.setup()
        self.assertIsNotNone(c.client)
        self.assertTrue(c.setup_done)

    def test_capacity_disk_size_successful(self, mock_ssh):
        c = storagecapacity.StorageCapacity(self.scn,self.ctx)

        mock_ssh.SSH().execute.return_value = (0, DISK_SIZE_SAMPLE_OUTPUT, '')
        c.run(self.result)
        expected_result = json.loads(DISK_SIZE_SAMPLE_OUTPUT)
        self.assertEqual(self.result, expected_result)

    def test_capacity_block_size_successful(self, mock_ssh):
        c = storagecapacity.StorageCapacity(self.scn,self.ctx)

        mock_ssh.SSH().execute.return_value = (0, BLOCK_SIZE_SAMPLE_OUTPUT, '')
        c.run(self.result)
        expected_result = json.loads(BLOCK_SIZE_SAMPLE_OUTPUT)
        self.assertEqual(self.result, expected_result)

    def test_capacity_block_utilization_successful(self, mock_ssh):
        c = storagecapacity.StorageCapacity(self.scn,self.ctx)

        mock_ssh.SSH().execute.return_value = (0, DISK_UTIL_SAMPLE_OUTPUT, '')
        c.run(self.result)
        expected_result = json.loads(DISK_UTIL_SAMPLE_OUTPUT)
        self.assertEqual(self.result, expected_result)

    def test_capacity_unsuccessful_script_error(self, mock_ssh):
        c = storagecapacity.StorageCapacity(self.scn,self.ctx)
        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, c.run, self.result)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
