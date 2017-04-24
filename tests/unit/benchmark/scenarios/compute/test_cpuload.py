#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.lmbench.Lmbench

from __future__ import absolute_import
import mock
import unittest
import os

from yardstick.benchmark.scenarios.compute import cpuload


@mock.patch('yardstick.benchmark.scenarios.compute.cpuload.ssh')
class CPULoadTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'cirros',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    def test_setup_mpstat_installed(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        l.setup()
        self.assertIsNotNone(l.client)
        self.assertTrue(l.setup_done)
        self.assertTrue(l.has_mpstat)

    def test_setup_mpstat_not_installed(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (127, '', '')

        l.setup()
        self.assertIsNotNone(l.client)
        self.assertTrue(l.setup_done)
        self.assertFalse(l.has_mpstat)

    def test_execute_command_success(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        l.setup()

        expected_result = 'abcdefg'
        mock_ssh.SSH.from_node().execute.return_value = (0, expected_result, '')
        result = l._execute_command("foo")
        self.assertEqual(result, expected_result)

    def test_execute_command_failed(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        l.setup()

        mock_ssh.SSH.from_node().execute.return_value = (127, '', 'abcdefg')
        self.assertRaises(RuntimeError, l._execute_command,
                          "cat /proc/loadavg")

    def test_get_loadavg(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        l.setup()

        mock_ssh.SSH.from_node().execute.return_value = \
            (0, '1.50 1.45 1.51 3/813 14322', '')
        result = l._get_loadavg()
        expected_result = \
            {'loadavg': ['1.50', '1.45', '1.51', '3/813', '14322']}
        self.assertEqual(result, expected_result)

    def test_get_cpu_usage_mpstat(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        l.setup()

        l.interval = 1
        l.count = 1
        mpstat_output = self._read_file("cpuload_sample_output1.txt")
        mock_ssh.SSH.from_node().execute.return_value = (0, mpstat_output, '')
        result = l._get_cpu_usage_mpstat()

        expected_result = \
            {"mpstat_minimum":
                {"cpu": {"%steal": "0.00", "%usr": "0.00", "%gnice": "0.00",
                         "%idle": "100.00", "%guest": "0.00",
                         "%iowait": "0.00", "%sys": "0.00", "%soft": "0.00",
                         "%irq": "0.00", "%nice": "0.00"},
                 "cpu0": {"%steal": "0.00", "%usr": "0.00", "%gnice": "0.00",
                          "%idle": "100.00", "%guest": "0.00",
                          "%iowait": "0.00", "%sys": "0.00", "%soft": "0.00",
                          "%irq": "0.00", "%nice": "0.00"}},
             "mpstat_average":
                {"cpu": {"%steal": "0.00", "%usr": "0.00", "%gnice": "0.00",
                         "%idle": "100.00", "%guest": "0.00",
                         "%iowait": "0.00", "%sys": "0.00", "%soft": "0.00",
                         "%irq": "0.00", "%nice": "0.00"},
                 "cpu0": {"%steal": "0.00", "%usr": "0.00", "%gnice": "0.00",
                          "%idle": "100.00", "%guest": "0.00",
                          "%iowait": "0.00", "%sys": "0.00", "%soft": "0.00",
                          "%irq": "0.00", "%nice": "0.00"}},
             "mpstat_maximun":
                {"cpu": {"%steal": "0.00", "%usr": "0.00", "%gnice": "0.00",
                         "%idle": "100.00", "%guest": "0.00",
                         "%iowait": "0.00", "%sys": "0.00", "%soft": "0.00",
                         "%irq": "0.00", "%nice": "0.00"},
                 "cpu0": {"%steal": "0.00", "%usr": "0.00", "%gnice": "0.00",
                          "%idle": "100.00", "%guest": "0.00",
                          "%iowait": "0.00", "%sys": "0.00", "%soft": "0.00",
                          "%irq": "0.00", "%nice": "0.00"}}}

        self.assertDictEqual(result, expected_result)

    def test_get_cpu_usage(self, mock_ssh):
        options = {
            "interval": 0,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        l.setup()

        l.interval = 0
        output = self._read_file("cpuload_sample_output2.txt")
        mock_ssh.SSH.from_node().execute.return_value = (0, output, '')
        result = l._get_cpu_usage()

        expected_result = \
            {'mpstat':
                {'cpu':
                    {'%steal': '0.00',
                     '%usr': '11.31',
                     '%gnice': '0.00',
                     '%idle': '81.78',
                     '%iowait': '0.18',
                     '%guest': '5.50',
                     '%sys': '1.19',
                     '%soft': '0.01',
                     '%irq': '0.00',
                     '%nice': '0.03'},
                 'cpu0':
                    {'%steal': '0.00',
                     '%usr': '20.00',
                     '%gnice': '0.00',
                     '%idle': '71.60',
                     '%iowait': '0.33',
                     '%guest': '6.61',
                     '%sys': '1.37',
                     '%soft': '0.06',
                     '%irq': '0.00',
                     '%nice': '0.03'}}}

        self.assertDictEqual(result, expected_result)

    def test_run_proc_stat(self, mock_ssh):
        options = {
            "interval": 1,
            "count": 1
        }

        args = {'options': options}

        l = cpuload.CPULoad(args, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (1, '', '')
        l.setup()

        l.interval = 0
        stat_output = self._read_file("cpuload_sample_output2.txt")
        mock_ssh.SSH.from_node().execute.side_effect = \
            [(0, '1.50 1.45 1.51 3/813 14322', ''), (0, stat_output, '')]

        l.run(self.result)
        expected_result = {
            'loadavg': ['1.50', '1.45', '1.51', '3/813', '14322'],
            'mpstat':
                {'cpu':
                    {'%steal': '0.00',
                     '%usr': '11.31',
                     '%gnice': '0.00',
                     '%idle': '81.78',
                     '%iowait': '0.18',
                     '%guest': '5.50',
                     '%sys': '1.19',
                     '%soft': '0.01',
                     '%irq': '0.00',
                     '%nice': '0.03'},
                 'cpu0':
                    {'%steal': '0.00',
                     '%usr': '20.00',
                     '%gnice': '0.00',
                     '%idle': '71.60',
                     '%iowait': '0.33',
                     '%guest': '6.61',
                     '%sys': '1.37',
                     '%soft': '0.06',
                     '%irq': '0.00',
                     '%nice': '0.03'}}}

        self.assertDictEqual(self.result, expected_result)

    def _read_file(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, filename)
        with open(output) as f:
            sample_output = f.read()
        return sample_output
