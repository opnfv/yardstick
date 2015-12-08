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
    @mock.patch('yardstick.cmd.commands.task._is_same_heat_context')
    def test_paras_nodes_host_target_same_context(self, mock_same_func, mock_context):
        nodes = {
            "host": "node1.LF",
            "target": "node2.LF"
        }
        scenario_cfg = {"nodes": nodes}
        server_info = {
            "ip": "8.8.8.8",
            "private_ip": "198.168.0.1"
        }
        mock_same_func.return_value = True
        mock_context.get_server.return_value = server_info
        context_cfg = task.paras_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["host"]["ipaddr"], server_info["private_ip"])
        self.assertEqual(context_cfg["target"]["ipaddr"], server_info["private_ip"])

    @mock.patch('yardstick.cmd.commands.task.Context')
    @mock.patch('yardstick.cmd.commands.task._is_same_heat_context')
    def test_paras_nodes_host_target_different_context(self, mock_same_func, mock_context):
        nodes = {
            "host": "node1.LF",
            "target": "node2.LF"
        }
        scenario_cfg = {"nodes": nodes}
        server_info = {
            "ip": "8.8.8.8",
            "private_ip": "198.168.0.1"
        }
        mock_same_func.return_value = False
        mock_context.get_server.return_value = server_info
        context_cfg = task.paras_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["host"]["ipaddr"], server_info["ip"])
        self.assertEqual(context_cfg["target"]["ipaddr"], server_info["ip"])

    @mock.patch('yardstick.cmd.commands.task.Context')
    def test_paras_nodes_target_ip(self, mock_context):
        nodes = {
            "host": "node1.LF",
            "target": "8.8.8.8"
        }
        scenario_cfg = {"nodes": nodes}
        server_info = {
            "ip": "8.8.8.8",
            "private_ip": "198.168.0.1"
        }
        mock_context.get_server.return_value = server_info
        context_cfg = task.paras_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["target"]["ipaddr"], server_info["ip"])
