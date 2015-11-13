#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.monitor.monitor_api

import mock
import unittest

from yardstick.benchmark.scenarios.availability.monitor import monitor_api

@mock.patch('yardstick.benchmark.scenarios.availability.monitor.monitor_api.subprocess')
class MonitorApiTestCase(unittest.TestCase):

    def test__fun_execute_shell_command_successful(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.return_value = (0, 'unittest')
        exitcode, output = monitor_api._execute_shell_command(cmd)
        self.assertEqual(exitcode, 0)

    def test__fun_execute_shell_command_fail_cmd_exception(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.side_effect = RuntimeError
        exitcode, output = monitor_api._execute_shell_command(cmd)
        self.assertEqual(exitcode, -1)

    def test__monitor_api_one_request_successful(self, mock_subprocess):
        mock_subprocess.check_output.return_value = (0, 'unittest')
        config = {
            'monitor_api': 'nova image-list',
            'monitor_type': 'openstack-api',
        }
        instance = monitor_api.MonitorApi(config)
        ret = instance.one_request()
        self.assertEqual(ret, 0)
