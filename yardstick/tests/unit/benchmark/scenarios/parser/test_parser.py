#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.parser import parser


@mock.patch('yardstick.benchmark.scenarios.parser.parser.subprocess')
class ParserTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_parser_successful_setup(self, mock_subprocess):

        p = parser.Parser({}, {})
        mock_subprocess.call().return_value = 0
        p.setup()
        self.assertTrue(p.setup_done)

    def test_parser_successful(self, mock_subprocess):
        args = {
            'options': {'yangfile': '/root/yardstick/samples/yang.yaml',
                        'toscafile': '/root/yardstick/samples/tosca.yaml'},
        }
        p = parser.Parser(args, {})
        result = {}
        mock_subprocess.call().return_value = 0
        sample_output = '{"yangtotosca": "success"}'

        p.run(result)
        expected_result = (  # pylint: disable=unused-variable
            jsonutils.loads(sample_output))


    def test_parser_teardown_successful(self, mock_subprocess):

        p = parser.Parser({}, {})
        mock_subprocess.call().return_value = 0
        p.teardown()
        self.assertTrue(p.teardown_done)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
