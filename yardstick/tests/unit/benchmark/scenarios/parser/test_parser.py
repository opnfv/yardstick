##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import subprocess

import unittest
import mock

from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.parser import parser


class ParserTestCase(unittest.TestCase):

    def setUp(self):
        args = {
            'options': {'yangfile': '/root/yardstick/samples/yang.yaml',
                        'toscafile': '/root/yardstick/samples/tosca.yaml'},
        }
        self.scenario = parser.Parser(scenario_cfg=args, context_cfg={})

        self._mock_popen = mock.patch.object(subprocess, 'Popen')
        self.mock_popen = self._mock_popen.start()
        self._mock_call = mock.patch.object(subprocess, 'call')
        self.mock_call = self._mock_call.start()

        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_popen.stop()
        self._mock_call.stop()

    def test_setup_successful(self):

        self.mock_call.return_value = 0
        self.scenario.setup()
        self.assertTrue(self.scenario.setup_done)

    def test_run_successful(self):

        result = {}

        self.mock_popen().returncode = 0

        expected_result = jsonutils.loads('{"yangtotosca": "success"}')

        self.scenario.run(result)
        self.assertEqual(result, expected_result)

    def test_run_fail(self):
        result = {}

        self.mock_popen().returncode = 1
        expected_result = jsonutils.loads('{"yangtotosca": "fail"}')

        self.scenario.run(result)
        self.assertEqual(result, expected_result)

    def test_teardown_successful(self):

        self.mock_call.return_value = 0
        self.scenario.teardown()
        self.assertTrue(self.scenario.teardown_done)
