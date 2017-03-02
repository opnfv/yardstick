#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.plugintest.PluginTest

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.compute import plugintest


@mock.patch('yardstick.benchmark.scenarios.compute.plugintest.ssh')
class PluginTestTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'nodes': {
                'host1': {
                    'ip': '172.16.0.137',
                    'user': 'cirros',
                    'key_filename': "mykey.key",
                    'password': "root"
                },
            }
        }

        self.result = {}

    def test_sample_successful_setup(self, mock_ssh):
        s = plugintest.PluginTest({}, self.ctx)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        s.setup()
        self.assertIsNotNone(s.client)
        self.assertTrue(s.setup_done)

    def test_sample_successful(self, mock_ssh):
        s = plugintest.PluginTest({}, self.ctx)

        sample_output = '{"Test Output": "Hello world!"}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        s.run(self.result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(self.result, expected_result)

    def test_sample_unsuccessful_script_error(self, mock_ssh):
        s = plugintest.PluginTest({}, self.ctx)

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, s.run, self.result)
