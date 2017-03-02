#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.core.plugin
from __future__ import absolute_import
import os
from os.path import dirname as dirname

try:
    from unittest import mock
except ImportError:
    import mock
import unittest

from yardstick.benchmark.core import plugin


class Arg(object):

    def __init__(self):
        # self.input_file = ('plugin/sample_config.yaml',)
        self.input_file = [
            os.path.join(os.path.abspath(
                dirname(dirname(dirname(dirname(dirname(__file__)))))),
                'plugin/sample_config.yaml')]


@mock.patch('yardstick.benchmark.core.plugin.ssh')
class pluginTestCase(unittest.TestCase):

    def setUp(self):
        self.result = {}

    def test_install(self, mock_ssh):
        p = plugin.Plugin()
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        input_file = Arg()
        p.install(input_file)
        expected_result = {}
        self.assertEqual(self.result, expected_result)

    def test_remove(self, mock_ssh):
        p = plugin.Plugin()
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        input_file = Arg()
        p.remove(input_file)
        expected_result = {}
        self.assertEqual(self.result, expected_result)

    def test_install_setup_run(self, mock_ssh):
        p = plugin.Plugin()
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
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
        p = plugin.Plugin()
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
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


def main():
    unittest.main()


if __name__ == '__main__':
    main()
