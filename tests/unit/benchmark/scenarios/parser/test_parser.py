#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.parser.Parser

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.parser import parser


@mock.patch('yardstick.benchmark.scenarios.parser.parser.subprocess')
class ParserTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_parser_successful_setup(self, mock_subprocess):

        scenario = parser.Parser({}, {})
        mock_subprocess.call().return_value = 0
        scenario.setup()
        self.assertTrue(scenario.setup_done)

    def test_parser_successful(self, mock_subprocess):
        args = {
            'options': {'yangfile': '/root/yardstick/samples/yang.yaml',
                        'toscafile': '/root/yardstick/samples/tosca.yaml'},
        }
        scenario = parser.Parser(scenario_cfg=args, context_cfg={})

        result = {}

        mock_subprocess.Popen = mock.Mock()
        mock_subprocess.Popen().returncode = 0

        sample_output = '{"yangtotosca": "success"}'
        expected_result = jsonutils.loads(sample_output)

        scenario.run(result)
        self.assertEqual(result, expected_result)

    def test_parser_fail(self, mock_subprocess):
        args = {
            'options': {'yangfile': '/root/yardstick/samples/yang.yaml',
                        'toscafile': '/root/yardstick/samples/tosca.yaml'},
        }
        scenario = parser.Parser(scenario_cfg=args, context_cfg={})

        result = {}

        mock_subprocess.Popen = mock.Mock()
        mock_subprocess.Popen().returncode = 1

        sample_output = '{"yangtotosca": "fail"}'
        expected_result = jsonutils.loads(sample_output)

        scenario.run(result)
        self.assertEqual(result, expected_result)

    def test_parser_teardown_successful(self, mock_subprocess):

        scenario = parser.Parser({}, {})
        mock_subprocess.call().return_value = 0
        scenario.teardown()
        self.assertTrue(scenario.teardown_done)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
