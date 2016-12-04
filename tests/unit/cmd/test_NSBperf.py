#!/usr/bin/env python

# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import absolute_import
import unittest
import mock
import subprocess
import os

from yardstick.cmd.NSBperf import handler, YardstickNSCli
from yardstick.cmd import NSBperf

@mock.patch('__builtin__.raw_input', return_value='0')
class TestHandler(unittest.TestCase):
    def test_handler(self, test):
        subprocess.call = mock.Mock(return_value=0)
        self.assertRaises(SystemExit, NSBperf.handler)

class TestYardstickNSCli(unittest.TestCase):
    def test___init__(self):
        yardstick_ns_cli = YardstickNSCli()

    def test_generate_final_report(self):
        yardstick_ns_cli = YardstickNSCli()
        test_case = "tc_baremetal_rfc2544_ipv4_1flow_1518B.yaml"
        subprocess.call(["touch", "/tmp/yardstick.out"])
        self.assertIsNone(yardstick_ns_cli.generate_final_report(test_case))

    def test_generate_kpi_results(self):
        yardstick_ns_cli = YardstickNSCli()
        tkey = "cpu"
        tgen = {"cpu": {"ipc": 0}}
        self.assertIsNone(yardstick_ns_cli.generate_kpi_results(tkey, tgen))
