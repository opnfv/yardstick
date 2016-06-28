#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.cmd.commands.plugin

import mock
import unittest

from yardstick.cmd.commands import plugin


class Arg(object):
    def __init__(self):
        self.input_file = ('plugin/sample_config.yaml',)


@mock.patch('yardstick.cmd.commands.plugin.ssh')
class pluginCommandsTestCase(unittest.TestCase):

    def setUp(self):
        self.result = {}

    def test_do_install(self, mock_ssh):
        p = plugin.PluginCommands()
        mock_ssh.SSH().execute.return_value = (0, '', '')
        input_file = Arg()
        p.do_install(input_file)
        expected_result = {}
        self.assertEqual(self.result, expected_result)

    def test_do_remove(self, mock_ssh):
        p = plugin.PluginCommands()
        mock_ssh.SSH().execute.return_value = (0, '', '')
        input_file = Arg()
        p.do_remove(input_file)
        expected_result = {}
        self.assertEqual(self.result, expected_result)

    def test_install_setup_run(self, mock_ssh):
        p = plugin.PluginCommands()
        mock_ssh.SSH().execute.return_value = (0, '', '')
        plugins = {
            "name": "sample"
        }
        deployment = {
            "ip": "10.1.0.50",
            "user": "root",
            "password": "root"
        }
        plugin_name = plugins.get("name")
        p._install_setup(plugin_name, deployment)
        self.assertIsNotNone(p.client)

        p._run(plugin_name)
        expected_result = {}
        self.assertEqual(self.result, expected_result)

    def test_remove_setup_run(self, mock_ssh):
        p = plugin.PluginCommands()
        mock_ssh.SSH().execute.return_value = (0, '', '')
        plugins = {
            "name": "sample"
        }
        deployment = {
            "ip": "10.1.0.50",
            "user": "root",
            "password": "root"
        }
        plugin_name = plugins.get("name")
        p._remove_setup(plugin_name, deployment)
        self.assertIsNotNone(p.client)

        p._run(plugin_name)
        expected_result = {}
        self.assertEqual(self.result, expected_result)
