#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.monitor

import mock
import unittest

from yardstick.benchmark.scenarios.availability import monitor

@mock.patch('yardstick.benchmark.scenarios.availability.monitor.subprocess')
class MonitorTestCase(unittest.TestCase):

    def test__fun_execute_shell_command_successful(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.return_value = (0, 'unittest')
        exitcode, output = monitor._execute_shell_command(cmd)
        self.assertEqual(exitcode, 0)

    def test__fun_execute_shell_command_fail_cmd_exception(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.side_effect = RuntimeError
        exitcode, output = monitor._execute_shell_command(cmd)
        self.assertEqual(exitcode, -1)

    def test__fun_monitor_process_successful(self, mock_subprocess):
        config = {
            'monitor_cmd':'env',
            'duration':0
        }
        mock_queue = mock.Mock()
        mock_event = mock.Mock()

        mock_subprocess.check_output.return_value = (0, 'unittest')
        monitor._monitor_process(config, mock_queue, mock_event)

    def test__fun_monitor_process_fail_cmd_execute_error(self, mock_subprocess):
        config = {
            'monitor_cmd':'env',
            'duration':0
        }
        mock_queue = mock.Mock()
        mock_event = mock.Mock()

        mock_subprocess.check_output.side_effect = RuntimeError
        monitor._monitor_process(config, mock_queue, mock_event)

    def test__fun_monitor_process_fail_no_monitor_cmd(self, mock_subprocess):
        config = {
            'duration':0
        }
        mock_queue = mock.Mock()
        mock_event = mock.Mock()

        mock_subprocess.check_output.return_value = (-1, 'unittest')
        monitor._monitor_process(config, mock_queue, mock_event)

    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.multiprocessing')
    def test_monitor_all_successful(self, mock_multip, mock_subprocess):
        config = {
            'monitor_cmd':'env',
            'duration':0
        }
        p = monitor.Monitor()
        p.setup(config)
        mock_multip.Queue().get.return_value = 'started'
        p.start()

        result = "monitor unitest"
        mock_multip.Queue().get.return_value = result
        p.stop()

        ret = p.get_result()

        self.assertEqual(result, ret)
