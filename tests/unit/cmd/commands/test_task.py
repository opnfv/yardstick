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
    def test_paras_nodes_host_target_same_context(self, mock_context):
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
        context_cfg = task.paras_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["host"], server_info)
        self.assertEqual(context_cfg["target"], server_info)
