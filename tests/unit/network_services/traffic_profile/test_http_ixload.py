# Copyright (c) 2017 Intel Corporation
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


from __future__ import absolute_import
import unittest
import mock
import runpy

from oslo_serialization import jsonutils

from yardstick.network_services.traffic_profile import http_ixload


class TestIxLoadTrafficGen(unittest.TestCase):

    def test_parse_run_test(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        self.assertEqual(testinput, ixload.testinput)
        self.assertEqual(ixload.ports_to_reassign, [
            ["IXIA_CHASSIS", "CARD", 1],
            ["IXIA_CHASSIS", "CARD", 2],
            ["IXIA_CHASSIS", "CARD", 3],
        ])

    def test_get_ports_reassing(self):
        ports = [
            ["IXIA_CHASSIS", "CARD", 1],
            ["IXIA_CHASSIS", "CARD", 2],
            ["IXIA_CHASSIS", "CARD", 3],
        ]
        formatted = http_ixload.IXLOADHttpTest.get_ports_reassign(ports)
        self.assertEqual(formatted, [
            "IXIA_CHASSIS;CARD;1",
            "IXIA_CHASSIS;CARD;2",
            "IXIA_CHASSIS;CARD;3",
        ])

    def test_reassign_ports(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        repository = mock.Mock()
        test = mock.MagicMock()
        test.setPorts = mock.Mock()
        ports_to_reassign = [(1, 2, 3), (1, 2, 4)]
        ixload.get_ports_reassign = mock.Mock(return_value=["1;2;3"])
        self.assertIsNone(ixload.reassign_ports(test, repository,
                                                ports_to_reassign))

    def test_reassign_ports_error(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        repository = mock.Mock()
        test = "test"
        ports_to_reassign = [(1, 2, 3), (1, 2, 4)]
        ixload.get_ports_reassign = mock.Mock(return_value=["1;2;3"])
        ixload.ixLoad = mock.MagicMock()
        ixload.ixLoad.delete = mock.Mock()
        ixload.ixLoad.disconnect = mock.Mock()
        self.assertRaises(Exception, ixload.reassign_ports,
                          test, repository, ports_to_reassign)

    def test_stat_collector(self):
        args = [0, 1]
        self.assertIsNone(
            http_ixload.IXLOADHttpTest.stat_collector(*args))

    def test_IxL_StatCollectorCommand(self):
        args = [[0, 1, 2, 3], [0, 1, 2, 3]]
        self.assertIsNone(
            http_ixload.IXLOADHttpTest.IxL_StatCollectorCommand(*args))

    def test_set_results_dir(self):
        test_stat_collector = mock.MagicMock()
        test_stat_collector.setResultDir = mock.Mock()
        results_on_windows = "c:/Results"
        self.assertIsNone(
            http_ixload.IXLOADHttpTest.set_results_dir(test_stat_collector,
                                                       results_on_windows))

    def test_set_results_dir_error(self):
        test_stat_collector = ""
        results_on_windows = "c:/Results"
        self.assertRaises(Exception,
                          http_ixload.IXLOADHttpTest.set_results_dir,
                          test_stat_collector, results_on_windows)

    def test_load_config_file(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.ixLoad = mock.MagicMock()
        ixload.ixLoad.new = mock.Mock(return_value="")
        self.assertIsNotNone(ixload.load_config_file("ixload.cfg"))

    def test_load_config_file_error(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.ixLoad = "test"
        self.assertRaises(Exception, ixload.load_config_file, "ixload.cfg")

    def test_start_http_test_error(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.get_ixload_obj = mock.Mock(return_value=[mock.MagicMock(),
                                                        mock.MagicMock()])
        ixload.ixLoad = "error"
        self.assertRaises(Exception, ixload.start_http_test, None)

    def test_start_http_test(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.get_ixload_obj = mock.Mock(return_value=[mock.MagicMock(),
                                                        mock.MagicMock()])
        ixload.ixLoad = mock.MagicMock()
        ixload.ixLoad.connect = mock.Mock()
        ixload.ixLoad.new = mock.Mock()
        ixload.ixLoad.ixLogger = mock.Mock()
        ixload.ixLoad.ixLogger.kLevelDebug = 1
        ixload.ixLoad.ixLogger.kLevelInfo = 1
        ixload.stat_utils = mock.MagicMock()
        ixload.load_config_file = mock.MagicMock()
        self.assertIsNone(ixload.start_http_test(True))

    def test_start_http_test_error1(self):
        ports = [1, 2, 3]
        testinput = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(testinput)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.get_ixload_obj = mock.Mock(return_value=[mock.MagicMock(),
                                                        mock.MagicMock()])
        ixload.ixLoad = mock.MagicMock()
        ixload.ixLoad.connect = mock.Mock()
        ixload.ixLoad.new = mock.Mock()
        ixload.ixLoad.ixLogger = mock.Mock()
        ixload.ixLoad.ixLogger.kLevelDebug = 1
        ixload.ixLoad.ixLogger.kLevelInfo = 1
        ixload.stat_utils = mock.MagicMock()
        ixload.reassign_ports = "error"
        self.assertRaises(Exception, ixload.start_http_test, True)

    @mock.patch("yardstick.network_services.traffic_profile.http_ixload.IXLOADHttpTest")
    def test_main(self, IXLOADHttpTest):
        args = ["1", "2", "3"]
        http_ixload.main(args)
