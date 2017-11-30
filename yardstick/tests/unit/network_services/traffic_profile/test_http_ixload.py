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

import unittest
import mock

from oslo_serialization import jsonutils

from yardstick.network_services.traffic_profile import http_ixload
from yardstick.network_services.traffic_profile.http_ixload import \
    join_non_strings, validate_non_string_sequence


class TestJoinNonStrings(unittest.TestCase):

    def test_validate_non_string_sequence(self):
        self.assertEqual(validate_non_string_sequence([1, 2, 3]), [1, 2, 3])
        self.assertIsNone(validate_non_string_sequence('123'))
        self.assertIsNone(validate_non_string_sequence(1))

        self.assertEqual(validate_non_string_sequence(1, 2), 2)
        self.assertEqual(validate_non_string_sequence(1, default=2), 2)

        with self.assertRaises(RuntimeError):
            validate_non_string_sequence(1, raise_exc=RuntimeError)

    def test_join_non_strings(self):
        self.assertEqual(join_non_strings(':'), '')
        self.assertEqual(join_non_strings(':', 'a'), 'a')
        self.assertEqual(join_non_strings(':', 'a', 2, 'c'), 'a:2:c')
        self.assertEqual(join_non_strings(':', ['a', 2, 'c']), 'a:2:c')
        self.assertEqual(join_non_strings(':', 'abc'), 'abc')


class TestIxLoadTrafficGen(unittest.TestCase):

    def test_parse_run_test(self):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(test_input)
        ixload = http_ixload.IXLOADHttpTest(j)
        self.assertDictEqual(ixload.test_input, test_input)
        self.assertIsNone(ixload.parse_run_test())
        self.assertEqual(ixload.ports_to_reassign, [
            ["IXIA_CHASSIS", "CARD", 1],
            ["IXIA_CHASSIS", "CARD", 2],
            ["IXIA_CHASSIS", "CARD", 3],
        ])

    def test_format_ports_for_reassignment(self):
        ports = [
            ["IXIA_CHASSIS", "CARD", 1],
            ["IXIA_CHASSIS", "CARD", 2],
            ["IXIA_CHASSIS", "CARD", 3],
        ]
        formatted = http_ixload.IXLOADHttpTest.format_ports_for_reassignment(ports)
        self.assertEqual(formatted, [
            "IXIA_CHASSIS;CARD;1",
            "IXIA_CHASSIS;CARD;2",
            "IXIA_CHASSIS;CARD;3",
        ])

    def test_reassign_ports(self):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(test_input)
        ixload = http_ixload.IXLOADHttpTest(j)
        repository = mock.Mock()
        test = mock.MagicMock()
        test.setPorts = mock.Mock()
        ports_to_reassign = [(1, 2, 3), (1, 2, 4)]
        ixload.format_ports_for_reassignment = mock.Mock(return_value=["1;2;3"])
        self.assertIsNone(ixload.reassign_ports(test, repository, ports_to_reassign))

    def test_reassign_ports_error(self):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(test_input)
        ixload = http_ixload.IXLOADHttpTest(j)
        repository = mock.Mock()
        test = "test"
        ports_to_reassign = [(1, 2, 3), (1, 2, 4)]
        ixload.format_ports_for_reassignment = mock.Mock(return_value=["1;2;3"])
        ixload.ix_load = mock.MagicMock()
        ixload.ix_load.delete = mock.Mock()
        ixload.ix_load.disconnect = mock.Mock()
        with self.assertRaises(Exception):
            ixload.reassign_ports(test, repository, ports_to_reassign)

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
        with self.assertRaises(Exception):
            http_ixload.IXLOADHttpTest.set_results_dir(test_stat_collector, results_on_windows)

    def test_load_config_file(self):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(test_input)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.ix_load = mock.MagicMock()
        ixload.ix_load.new = mock.Mock(return_value="")
        self.assertIsNotNone(ixload.load_config_file("ixload.cfg"))

    def test_load_config_file_error(self):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }
        j = jsonutils.dump_as_bytes(test_input)
        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.ix_load = "test"
        with self.assertRaises(Exception):
            ixload.load_config_file("ixload.cfg")

    @mock.patch('yardstick.network_services.traffic_profile.http_ixload.StatCollectorUtils')
    @mock.patch('yardstick.network_services.traffic_profile.http_ixload.IxLoad')
    def test_start_http_test_connect_error(self, mock_ixload_type, *args):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }

        j = jsonutils.dump_as_bytes(test_input)

        mock_ixload_type.return_value.connect.side_effect = RuntimeError

        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.results_on_windows = 'windows_result_dir'
        ixload.result_dir = 'my_result_dir'

        with self.assertRaises(RuntimeError):
            ixload.start_http_test()

    @mock.patch('yardstick.network_services.traffic_profile.http_ixload.IxLoad')
    @mock.patch('yardstick.network_services.traffic_profile.http_ixload.StatCollectorUtils')
    def test_start_http_test(self, *args):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }

        j = jsonutils.dump_as_bytes(test_input)

        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.results_on_windows = 'windows_result_dir'
        ixload.result_dir = 'my_result_dir'
        ixload.load_config_file = mock.MagicMock()

        self.assertIsNone(ixload.start_http_test())

    @mock.patch('yardstick.network_services.traffic_profile.http_ixload.IxLoad')
    @mock.patch('yardstick.network_services.traffic_profile.http_ixload.StatCollectorUtils')
    def test_start_http_test_reassign_error(self, *args):
        ports = [1, 2, 3]
        test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
        }

        j = jsonutils.dump_as_bytes(test_input)

        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.load_config_file = mock.MagicMock()

        reassign_ports = mock.Mock(side_effect=RuntimeError)
        ixload.reassign_ports = reassign_ports
        ixload.results_on_windows = 'windows_result_dir'
        ixload.result_dir = 'my_result_dir'

        ixload.start_http_test()
        reassign_ports.assert_called_once()

    @mock.patch("yardstick.network_services.traffic_profile.http_ixload.IXLOADHttpTest")
    def test_main(self, *args):
        args = ["1", "2", "3"]
        http_ixload.main(args)
