# Copyright (c) 2017-2019 Intel Corporation
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

    def setUp(self):
        ports = [1, 2, 3]
        self.test_input = {
            "remote_server": "REMOTE_SERVER",
            "ixload_cfg": "IXLOAD_CFG",
            "result_dir": "RESULT_DIR",
            "ixia_chassis": "IXIA_CHASSIS",
            "IXIA": {
                "card": "CARD",
                "ports": ports,
            },
            'links_param': {
                "uplink_0": {
                    "ip": {"address": "address",
                           "gateway": "gateway",
                           "subnet_prefix": "subnet_prefix",
                           "mac": "mac"
                           }}}
        }

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
            'links_param': {}
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
        self.assertEqual({}, ixload.links_param)

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
            'links_param': {}
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
            'links_param': {}
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
            'links_param': {}
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
            'links_param': {}
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
            'links_param': {}
        }

        j = jsonutils.dump_as_bytes(test_input)

        mock_ixload_type.return_value.connect.side_effect = RuntimeError

        ixload = http_ixload.IXLOADHttpTest(j)
        ixload.results_on_windows = 'windows_result_dir'
        ixload.result_dir = 'my_result_dir'

        with self.assertRaises(RuntimeError):
            ixload.start_http_test()

    def test_update_config(self):
        net_taraffic_0 = mock.Mock()
        net_taraffic_0.name = "HTTP client@uplink_0"
        net_taraffic_1 = mock.Mock()
        net_taraffic_1.name = "HTTP client@uplink_1"

        community_list = [net_taraffic_0, net_taraffic_1, Exception]
        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        ixload.links_param = {"uplink_0": {"ip": {},
                                           "http_client": {}}}

        ixload.test = mock.Mock()
        ixload.test.communityList = community_list

        ixload.update_network_param = mock.Mock()
        ixload.update_http_client_param = mock.Mock()

        ixload.update_config()

        ixload.update_network_param.assert_called_once_with(net_taraffic_0, {})
        ixload.update_http_client_param.assert_called_once_with(net_taraffic_0,
                                                                {})

    def test_update_network_mac_address(self):
        ethernet = mock.MagicMock()
        net_traffic = mock.Mock()
        net_traffic.network.getL1Plugin.return_value = ethernet

        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        ix_net_l2_ethernet_plugin = ethernet.childrenList[0]
        ix_net_ip_v4_v6_plugin = ix_net_l2_ethernet_plugin.childrenList[0]
        ix_net_ip_v4_v6_range = ix_net_ip_v4_v6_plugin.rangeList[0]

        ixload.update_network_mac_address(net_traffic, "auto")
        ix_net_ip_v4_v6_range.config.assert_called_once_with(
            autoMacGeneration=True)

        ixload.update_network_mac_address(net_traffic, "00:00:00:00:00:01")
        ix_net_ip_v4_v6_range.config.assert_called_with(
            autoMacGeneration=False)
        mac_range = ix_net_ip_v4_v6_range.getLowerRelatedRange("MacRange")
        mac_range.config.assert_called_once_with(mac="00:00:00:00:00:01")

        net_traffic.network.getL1Plugin.return_value = Exception

        with self.assertRaises(http_ixload.InvalidRxfFile):
            ixload.update_network_mac_address(net_traffic, "auto")

    def test_update_network_address(self):
        ethernet = mock.MagicMock()
        net_traffic = mock.Mock()
        net_traffic.network.getL1Plugin.return_value = ethernet

        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        ix_net_l2_ethernet_plugin = ethernet.childrenList[0]
        ix_net_ip_v4_v6_plugin = ix_net_l2_ethernet_plugin.childrenList[0]
        ix_net_ip_v4_v6_range = ix_net_ip_v4_v6_plugin.rangeList[0]

        ixload.update_network_address(net_traffic, "address", "gateway",
                                      "prefix")
        ix_net_ip_v4_v6_range.config.assert_called_once_with(
            prefix="prefix",
            ipAddress="address",
            gatewayAddress="gateway")

        net_traffic.network.getL1Plugin.return_value = Exception

        with self.assertRaises(http_ixload.InvalidRxfFile):
            ixload.update_network_address(net_traffic, "address", "gateway",
                                          "prefix")

    def test_update_network_param(self):
        net_traffic = mock.Mock()

        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        ixload.update_network_address = mock.Mock()
        ixload.update_network_mac_address = mock.Mock()

        param = {"address": "address",
                 "gateway": "gateway",
                 "subnet_prefix": "subnet_prefix",
                 "mac": "mac"
                 }

        ixload.update_network_param(net_traffic, param)

        ixload.update_network_address.assert_called_once_with(net_traffic,
                                                              "address",
                                                              "gateway",
                                                              "subnet_prefix")

        ixload.update_network_mac_address.assert_called_once_with(
            net_traffic,
            "mac")

    def test_update_http_client_param(self):
        net_traffic = mock.Mock()

        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        ixload.update_page_size = mock.Mock()
        ixload.update_user_count = mock.Mock()

        param = {"page_object": "page_object",
                 "simulated_users": "simulated_users"}

        ixload.update_http_client_param(net_traffic, param)

        ixload.update_page_size.assert_called_once_with(net_traffic,
                                                        "page_object")
        ixload.update_user_count.assert_called_once_with(net_traffic,
                                                         "simulated_users")

    def test_update_page_size(self):
        activity = mock.MagicMock()
        net_traffic = mock.Mock()

        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        net_traffic.activityList = [activity]
        ix_http_command = activity.agent.actionList[0]
        ixload.update_page_size(net_traffic, "page_object")
        ix_http_command.config.assert_called_once_with(
            pageObject="page_object")

        net_traffic.activityList = []
        with self.assertRaises(http_ixload.InvalidRxfFile):
            ixload.update_page_size(net_traffic, "page_object")

    def test_update_user_count(self):
        activity = mock.MagicMock()
        net_traffic = mock.Mock()

        ixload = http_ixload.IXLOADHttpTest(
            jsonutils.dump_as_bytes(self.test_input))

        net_traffic.activityList = [activity]
        ixload.update_user_count(net_traffic, 123)
        activity.config.assert_called_once_with(userObjectiveValue=123)

        net_traffic.activityList = []
        with self.assertRaises(http_ixload.InvalidRxfFile):
            ixload.update_user_count(net_traffic, 123)

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
            'links_param': {}
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
            'links_param': {}
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
