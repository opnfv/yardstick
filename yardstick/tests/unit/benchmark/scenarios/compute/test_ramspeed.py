#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.ramspeed.Ramspeed

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.common import utils
from yardstick.benchmark.scenarios.compute import ramspeed


@mock.patch('yardstick.benchmark.scenarios.compute.ramspeed.ssh')
class RamspeedTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_ramspeed_successful_setup(self, mock_ssh):

        r = ramspeed.Ramspeed({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        r.setup()
        self.assertIsNotNone(r.client)
        self.assertTrue(r.setup_done, True)

    def test_ramspeed_successful__run_no_sla(self, mock_ssh):

        options = {
            "test_id": 1,
            "load": 16,
            "block_size": 32
        }
        args = {"options": options}
        r = ramspeed.Ramspeed(args, self.ctx)

        sample_output = '{"Result": [{"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 1, "Bandwidth(MBps)": 19909.18}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 2, "Bandwidth(MBps)": 19873.89},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 4, "Bandwidth(MBps)":\
 19907.56}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 8,\
 "Bandwidth(MBps)": 19906.94}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 16, "Bandwidth(MBps)": 19881.74}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 32, "Bandwidth(MBps)": 19395.65},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 64, "Bandwidth(MBps)":\
 17623.14}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 128,\
 "Bandwidth(MBps)": 17677.36}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 256, "Bandwidth(MBps)": 16113.49}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 512, "Bandwidth(MBps)": 14659.19},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 1024, "Bandwidth(MBps)":\
 14680.75}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 2048,\
 "Bandwidth(MBps)": 14756.45}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 4096, "Bandwidth(MBps)": 14604.44}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 8192, "Bandwidth(MBps)": 14159.86},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 16384,\
 "Bandwidth(MBps)": 14128.94}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 32768, "Bandwidth(MBps)": 8340.85}]}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        r.run(self.result)
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        self.assertEqual(self.result, expected_result)

    def test_ramspeed_successful_run_sla(self, mock_ssh):

        options = {
            "test_id": 1,
            "load": 16,
            "block_size": 32
        }
        args = {"options": options, "sla": {"min_bandwidth": 6000}}
        r = ramspeed.Ramspeed(args, self.ctx)

        sample_output = '{"Result": [{"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 1, "Bandwidth(MBps)": 19909.18}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 2, "Bandwidth(MBps)": 19873.89},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 4, "Bandwidth(MBps)":\
 19907.56}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 8,\
 "Bandwidth(MBps)": 19906.94}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 16, "Bandwidth(MBps)": 19881.74}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 32, "Bandwidth(MBps)": 19395.65},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 64, "Bandwidth(MBps)":\
 17623.14}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 128,\
 "Bandwidth(MBps)": 17677.36}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 256, "Bandwidth(MBps)": 16113.49}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 512, "Bandwidth(MBps)": 14659.19},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 1024, "Bandwidth(MBps)":\
 14680.75}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 2048,\
 "Bandwidth(MBps)": 14756.45}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 4096, "Bandwidth(MBps)": 14604.44}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 8192, "Bandwidth(MBps)": 14159.86},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 16384,\
 "Bandwidth(MBps)": 14128.94}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 32768, "Bandwidth(MBps)": 8340.85}]}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        r.run(self.result)
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        self.assertEqual(self.result, expected_result)

    def test_ramspeed_unsuccessful_run_sla(self, mock_ssh):
        options = {
            "test_id": 1,
            "load": 8,
            "block_size": 64
        }
        args = {"options": options, "sla": {"min_bandwidth": 100000}}
        r = ramspeed.Ramspeed(args, self.ctx)

        sample_output = '{"Result": [{"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 1, "Bandwidth(MBps)": 5000.18}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 2, "Bandwidth(MBps)": 5000.89},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 4,\
 "Bandwidth(MBps)": 5000.56}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 8, "Bandwidth(MBps)": 19906.94}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 16, "Bandwidth(MBps)": 19881.74},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 32,\
 "Bandwidth(MBps)": 19395.65}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 64, "Bandwidth(MBps)": 17623.14}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 128, "Bandwidth(MBps)": 17677.36},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 256, "Bandwidth(MBps)":\
 16113.49}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 512,\
 "Bandwidth(MBps)": 14659.19}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 1024, "Bandwidth(MBps)": 14680.75}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 2048, "Bandwidth(MBps)": 14756.45},\
 {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 4096, "Bandwidth(MBps)":\
 14604.44}, {"Test_type": "INTEGER & WRITING", "Block_size(kb)": 8192,\
 "Bandwidth(MBps)": 14159.86}, {"Test_type": "INTEGER & WRITING",\
 "Block_size(kb)": 16384, "Bandwidth(MBps)": 14128.94}, {"Test_type":\
 "INTEGER & WRITING", "Block_size(kb)": 32768, "Bandwidth(MBps)": 8340.85}]}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, r.run, self.result)

    def test_ramspeed_unsuccessful_script_error(self, mock_ssh):
        options = {
            "test_id": 1,
            "load": 16,
            "block_size": 32
        }
        args = {"options": options}
        r = ramspeed.Ramspeed(args, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, r.run, self.result)

    def test_ramspeed_mem_successful_run_no_sla(self, mock_ssh):
        options = {
            "test_id": 3,
            "load": 16,
            "block_size": 32,
            "iteration": 1
        }
        args = {"options": options}
        r = ramspeed.Ramspeed(args, self.ctx)

        sample_output = '{"Result": [{"Test_type": "INTEGER Copy:",\
 "Bandwidth(MBps)": 8353.97}, {"Test_type": "INTEGER Scale:",\
 "Bandwidth(MBps)": 9078.59}, {"Test_type": "INTEGER Add:",\
 "Bandwidth(MBps)": 10057.48}, {"Test_type": "INTEGER Triad:",\
 "Bandwidth(MBps)": 10116.27}, {"Test_type": "INTEGER AVERAGE:",\
 "Bandwidth(MBps)": 9401.58}]}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        r.run(self.result)
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        self.assertEqual(self.result, expected_result)

    def test_ramspeed_mem_successful_run_sla(self, mock_ssh):
        options = {
            "test_id": 3,
            "load": 16,
            "block_size": 32,
            "iteration": 1
        }
        args = {"options": options, "sla": {"min_bandwidth": 6000}}
        r = ramspeed.Ramspeed(args, self.ctx)

        sample_output = '{"Result": [{"Test_type": "INTEGER Copy:",\
 "Bandwidth(MBps)": 8353.97}, {"Test_type": "INTEGER Scale:",\
 "Bandwidth(MBps)": 9078.59}, {"Test_type": "INTEGER Add:",\
 "Bandwidth(MBps)": 10057.48}, {"Test_type": "INTEGER Triad:",\
 "Bandwidth(MBps)": 10116.27}, {"Test_type": "INTEGER AVERAGE:",\
 "Bandwidth(MBps)": 9401.58}]}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        r.run(self.result)
        expected_result = utils.flatten_dict_key(jsonutils.loads(sample_output))
        self.assertEqual(self.result, expected_result)

    def test_ramspeed_mem_unsuccessful_run_sla(self, mock_ssh):
        options = {
            "test_id": 3,
            "load": 16,
            "block_size": 32,
            "iteration": 1
        }
        args = {"options": options, "sla": {"min_bandwidth": 86000}}
        r = ramspeed.Ramspeed(args, self.ctx)

        sample_output = '{"Result": [{"Test_type": "INTEGER Copy:",\
 "Bandwidth(MBps)": 4000.97}, {"Test_type": "INTEGER Scale:",\
 "Bandwidth(MBps)": 4400.59}, {"Test_type": "INTEGER Add:",\
 "Bandwidth(MBps)": 4300.48}, {"Test_type": "INTEGER Triad:",\
 "Bandwidth(MBps)": 1300.27}, {"Test_type": "INTEGER AVERAGE:",\
 "Bandwidth(MBps)": 2401.58}]}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, r.run, self.result)

    def test_ramspeed_unsuccessful_unknown_type_run(self, mock_ssh):
        options = {
            "test_id": 30,
            "load": 16,
            "block_size": 32
        }
        args = {'options': options}
        r = ramspeed.Ramspeed(args, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'No such type_id: 30 for \
                                               Ramspeed scenario')
        self.assertRaises(RuntimeError, r.run, self.result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
