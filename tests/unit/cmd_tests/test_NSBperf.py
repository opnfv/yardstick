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

from yardstick.cmd.NSBperf import YardstickNSCli
from yardstick.cmd import NSBperf


@mock.patch('six.moves.input', return_value='0')
class TestHandler(unittest.TestCase):
    def test_handler(self, test):
        subprocess.call = mock.Mock(return_value=0)
        self.assertRaises(SystemExit, NSBperf.sigint_handler)


class TestYardstickNSCli(unittest.TestCase):
    def test___init__(self):
        yardstick_ns_cli = YardstickNSCli()
        self.assertIsNotNone(yardstick_ns_cli)

    def test_generate_final_report(self):
        yardstick_ns_cli = YardstickNSCli()
        test_case = "tc_baremetal_rfc2544_ipv4_1flow_1518B.yaml"
        if os.path.isfile("/tmp/yardstick.out"):
            os.remove('/tmp/yardstick.out')
        self.assertIsNone(yardstick_ns_cli.generate_final_report(test_case))

    def test_generate_kpi_results(self):
        yardstick_ns_cli = YardstickNSCli()
        tkey = "cpu"
        tgen = {"cpu": {"ipc": 0}}
        self.assertIsNone(yardstick_ns_cli.generate_kpi_results(tkey, tgen))

    def test_generate_nfvi_results(self):
        yardstick_ns_cli = YardstickNSCli()
        nfvi = {"collect_stats": {"cpu": {"ipc": 0, "Hz": 2.6}}}
        self.assertIsNone(yardstick_ns_cli.generate_nfvi_results(nfvi))

    def test_handle_list_options(self):
        yardstick_ns_cli = YardstickNSCli()
        CLI_PATH = os.path.dirname(os.path.realpath(__file__))
        repo_dir = CLI_PATH + "/../../"
        test_path = os.path.join(repo_dir, "../samples/vnf_samples/nsut/")
        args = {"list_vnfs": True, "list": False}
        self.assertRaises(SystemExit, yardstick_ns_cli.handle_list_options,
                          args, test_path)
        args = {"list_vnfs": False, "list": True}
        self.assertRaises(SystemExit,
                          yardstick_ns_cli.handle_list_options,
                          args, test_path)

    def test_main(self):
        yardstick_ns_cli = YardstickNSCli()
        yardstick_ns_cli.parse_arguments = mock.Mock(return_value=0)
        yardstick_ns_cli.handle_list_options = mock.Mock(return_value=0)
        yardstick_ns_cli.terminate_if_less_options = mock.Mock(return_value=0)
        yardstick_ns_cli.run_test = mock.Mock(return_value=0)
        self.assertIsNone(yardstick_ns_cli.main())

    def test_parse_arguments(self):
        yardstick_ns_cli = YardstickNSCli()
        self.assertRaises(SystemExit, yardstick_ns_cli.parse_arguments)

    def test_run_test(self):
        cur_dir = os.getcwd()
        CLI_PATH = os.path.dirname(os.path.realpath(__file__))
        YARDSTICK_REPOS_DIR = os.path.join(CLI_PATH + "/../../")
        test_path = os.path.join(YARDSTICK_REPOS_DIR,
                                 "../samples/vnf_samples/nsut/")
        yardstick_ns_cli = YardstickNSCli()
        subprocess.check_output = mock.Mock(return_value=0)
        args = {"vnf": "vpe",
                "test": "tc_baremetal_rfc2544_ipv4_1flow_1518B.yaml"}
        self.assertEqual(None, yardstick_ns_cli.run_test(args, test_path))
        os.chdir(cur_dir)
        args = {"vnf": "vpe1"}
        self.assertEqual(None, yardstick_ns_cli.run_test(args, test_path))
        os.chdir(cur_dir)
        args = {"vnf": "vpe",
                "test": "tc_baremetal_rfc2544_ipv4_1flow_1518B.yaml."}
        self.assertEqual(None, yardstick_ns_cli.run_test(args, test_path))
        os.chdir(cur_dir)
        args = []
        self.assertEqual(None, yardstick_ns_cli.run_test(args, test_path))
        os.chdir(cur_dir)

    def test_terminate_if_less_options(self):
        yardstick_ns_cli = YardstickNSCli()
        args = {"vnf": False}
        self.assertRaises(SystemExit,
                          yardstick_ns_cli.terminate_if_less_options, args)

    def test_validate_input(self):
        yardstick_ns_cli = YardstickNSCli()
        self.assertEqual(1, yardstick_ns_cli.validate_input("", 4))
        NSBperf.input = lambda _: 'yes'
        self.assertEqual(1, yardstick_ns_cli.validate_input(5, 4))
        subprocess.call = mock.Mock(return_value=0)
        self.assertEqual(0, yardstick_ns_cli.validate_input(2, 4))
        subprocess.call = mock.Mock(return_value=0)
