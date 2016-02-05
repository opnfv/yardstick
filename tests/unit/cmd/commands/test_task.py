#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.cmd.commands.task

import mock
import unittest

from yardstick.cmd.commands import task


class TaskCommandsTestCase(unittest.TestCase):

    @mock.patch('yardstick.cmd.commands.task.Context')
    def test_parse_nodes_host_target_same_context(self, mock_context):
        nodes = {
            "host": "node1.LF",
            "target": "node2.LF"
        }
        scenario_cfg = {"nodes": nodes}
        server_info = {
           "ip": "10.20.0.3",
           "user": "root",
           "key_filename": "/root/.ssh/id_rsa"
        }
        mock_context.get_server.return_value = server_info
        context_cfg = task.parse_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["host"], server_info)
        self.assertEqual(context_cfg["target"], server_info)

    @mock.patch('yardstick.cmd.commands.task.Context')
    @mock.patch('yardstick.cmd.commands.task.base_runner')
    def test_run(self, mock_base_runner, mock_ctx):
        scenario = \
            {'host': 'athena.demo',
             'target': 'ares.demo',
             'runner':
                 {'duration': 60,
                  'interval': 1,
                  'type': 'Duration'
                 },
                 'type': 'Ping'}

        t = task.TaskCommands()
        runner = mock.Mock()
        runner.join.return_value = 0
        mock_base_runner.Runner.get.return_value = runner
        t._run([scenario], False, "yardstick.out")
        self.assertTrue(runner.run.called)

    @mock.patch('yardstick.cmd.commands.task.os')
    def test_check_precondition(self, mock_os):
        cfg = \
            {'precondition':
                 {'installer_type': 'compass',
                  'deploy_scenarios': 'os-nosdn'
                 }
            }

        t = task.TaskParser('/opt')
        mock_os.environ.get.side_effect = ['compass', 'os-nosdn']
        result = t._check_precondition(cfg)
        self.assertTrue(result)
