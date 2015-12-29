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

import mock
import unittest
import json

from yardstick.benchmark.scenarios.parser import parser


@mock.patch('yardstick.benchmark.scenarios.parser.parser.ssh')
class ParserTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "192.168.50.28",
                "user": "root",
                "key_filename": "mykey.key"
            }
        }

    def test_parser_successful_setup(self, mock_ssh):

        p = parser.Parser({}, self.ctx)
        p.setup()

        mock_ssh.SSH().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_parser_successful_no_sla(self, mock_ssh):

        p = parser.Parser({}, self.ctx)
        result = {}

        p.server = mock_ssh.SSH()

        sample_output = '{"result":"success"}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        p.run(result)
        expected_result = json.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_parser_unsuccessful_script_error(self, mock_ssh):

        p = parser.Parser({}, self.ctx)
        result = {}

        p.server = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
