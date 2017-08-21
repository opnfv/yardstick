#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Kanglin Yin and others
# 14_ykl@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.utils

import mock
import unittest

from yardstick.benchmark.scenarios.availability import util

@mock.patch('yardstick.benchmark.scenarios.availability.util.subprocess')
class ExecuteShellTestCase(unittest.TestCase):

    def setUp(self):
        self.param_config = {'serviceName': '$serviceName', 'value': 1}
        self.intermediate_variables = {'$serviceName': 'nova-api'}
        self.std_output = '| id       | 1                     |'
        self.cmd_config = {'cmd':'ls','param':'-a'}

    def test_util_build_command_shell(self,mock_subprocess):
        result = util.build_shell_command(self.param_config, True,
                                          self.intermediate_variables)
        self.assertEqual("nova-api" in result, True)

    def test_read_stdout_item(self,mock_subprocess):
        result = util.read_stdout_item(self.std_output,'id')
        self.assertEquals('1',result)

    def test_buildshellparams(self,mock_subprocess):
        result = util.buildshellparams(self.cmd_config,True)
        self.assertEquals('/bin/bash -s {0} {1}', result)

    def test__fun_execute_shell_command_successful(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.return_value = (0, 'unittest')
        exitcode, output = util.execute_shell_command(cmd)
        self.assertEqual(exitcode, 0)

    def test__fun_execute_shell_command_fail_cmd_exception(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.side_effect = RuntimeError
        exitcode, output = util.execute_shell_command(cmd)
        self.assertEqual(exitcode, -1)
