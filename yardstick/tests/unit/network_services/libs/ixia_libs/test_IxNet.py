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

import mock
import IxNetwork
import unittest

from yardstick.network_services.libs.ixia_libs.IxNet import IxNet


UPLINK = 'uplink'
DOWNLINK = 'downlink'


class TestIxNextgen(unittest.TestCase):

    def setUp(self):
        self.ixnet = mock.Mock()
        self.ixnet.execute = mock.Mock()

    def test___init__(self):
        ixnet_gen = IxNet.IxNextgen()
        self.assertIsNone(ixnet_gen.ixnet)
        self.assertTrue(isinstance(ixnet_gen._objRefs, dict))
        self.assertIsNone(ixnet_gen._cfg)
        self.assertIsNone(ixnet_gen._params)
        self.assertIsNone(ixnet_gen._bidir)

    def test___init__ixnet(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        self.assertIsNotNone(ixnet_gen.ixnet)

    @mock.patch.object(IxNetwork, 'IxNet')
    def test_connect(self, mock_ixnet):
        mock_ixnet.return_value = self.ixnet
        ixnet_gen = IxNet.IxNextgen()
        with mock.patch.object(ixnet_gen, 'get_config') as mock_config:
            mock_config.return_value = {'machine': 'machine_fake',
                                        'port': 'port_fake',
                                        'version': 12345}
            ixnet_gen.connect(mock.ANY)

        self.ixnet.connect.assert_called_once_with(
            'machine_fake', '-port', 'port_fake', '-version', '12345')
        mock_config.assert_called_once()

    def test_connect_invalid_config_no_machine(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen.get_config = mock.Mock(return_value={
            'port': 'port_fake',
            'version': '12345'})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_invalid_config_no_port(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen.get_config = mock.Mock(return_value={
            'machine': 'machine_fake',
            'version': '12345'})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_invalid_config_no_version(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen.get_config = mock.Mock(return_value={
            'machine': 'machine_fake',
            'port': 'port_fake'})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_no_config(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen.get_config = mock.Mock(return_value={})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_clear_config(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen.clear_config()
        self.ixnet.execute.assert_called_once_with('newConfig')

    def test_assign_ports_2_ports(self):
        self.ixnet.getAttribute.side_effect = ['up', 'down']

        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['2', '2'],
        }

        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen._cfg = config

        self.assertIsNone(ixnet_gen.assign_ports())

        self.assertEqual(self.ixnet.execute.call_count, 2)
        self.assertEqual(self.ixnet.commit.call_count, 4)
        self.assertEqual(self.ixnet.getAttribute.call_count, 2)

    @mock.patch.object(IxNet, 'log')
    def test_assign_ports_port_down(self, mock_log):
        self.ixnet.getAttribute.return_value = 'down'

        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['3', '4'],
        }
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen._cfg = config
        ixnet_gen.assign_ports()
        mock_log.warning.assert_called()

    def test_assign_ports_no_config(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen._cfg = {}

        self.assertRaises(KeyError, ixnet_gen.assign_ports)

    def test__create_traffic_item(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        self.ixnet.getRoot.return_value = 'rootyrootroot'
        self.ixnet.add.return_value = 'my_new_traffic_item'
        self.ixnet.remapIds.return_value = ['my_traffic_item_id']

        ixnet_gen._create_traffic_item()

        self.ixnet.add.assert_called_once_with(
            'rootyrootroot/traffic', 'trafficItem')
        self.ixnet.setMultiAttribute.assert_called_once_with(
            'my_new_traffic_item', '-name', 'RFC2544', '-trafficType', 'raw')
        self.assertEqual(2, self.ixnet.commit.call_count)
        self.ixnet.remapIds.assert_called_once_with('my_new_traffic_item')
        self.ixnet.setAttribute('my_traffic_item_id/tracking',
                                '-trackBy', 'trafficGroupId0')

    def test__create_flow_groups(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        self.ixnet.getRoot.return_value = 'rootyrootroot'
        ixnet_gen.ixnet.getList.side_effect = [['traffic_item'], ['1', '2']]
        ixnet_gen.ixnet.add.side_effect= ['endp1', 'endp2']
        ixnet_gen._create_flow_groups()
        ixnet_gen.ixnet.add.assert_has_calls([
            mock.call('traffic_item', 'endpointSet'),
            mock.call('traffic_item', 'endpointSet')])
        ixnet_gen.ixnet.setMultiAttribute.asser_has_calls([
            mock.call('endp1', '-sources', ['1/protocols'], '-destinations',
                      ['2/protocols']),
            mock.call('endp2', '-sources', ['2/protocols'], '-destinations',
                      ['1/protocols'])])

    def test__append_protocol_to_stack(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        self.ixnet.getRoot.return_value = 'my_root'

        ixnet_gen._append_procotol_to_stack('my_protocol', 'prev_element')
        self.ixnet.execute.assert_called_with(
            'append', 'prev_element',
            'my_root/traffic/protocolTemplate:"my_protocol"')

    def test__setup_config_elements(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)
        ixnet_gen.ixnet.getRoot.return_value = 'root_element'
        ixnet_gen.ixnet.getList.side_effect = [['traffic_item'],
                                               ['cfg_element']]
        with mock.patch.object(ixnet_gen, '_append_procotol_to_stack') as \
                mock_append_proto:
            ixnet_gen._setup_config_elements()
        mock_append_proto.assert_has_calls([
            mock.call(IxNet.PROTO_UDP, 'cfg_element/stack:"ethernet-1"'),
            mock.call(IxNet.PROTO_IPV4, 'cfg_element/stack:"ethernet-1"')])
        ixnet_gen.ixnet.setAttribute.assert_has_calls([
            mock.call('cfg_element/frameRateDistribution', '-portDistribution',
                      'splitRateEvenly'),
            mock.call('cfg_element/frameRateDistribution',
                      '-streamDistribution', 'splitRateEvenly')])

    @mock.patch.object(IxNet.IxNextgen, '_create_traffic_item')
    @mock.patch.object(IxNet.IxNextgen, '_create_flow_groups')
    @mock.patch.object(IxNet.IxNextgen, '_setup_config_elements')
    def test_create_traffic_model(self, mock__setup_config_elements,
                                  mock__create_flow_groups,
                                  mock__create_traffic_item):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        ixnet_gen.create_traffic_model()
        mock__create_traffic_item.assert_called_once()
        mock__create_flow_groups.assert_called_once()
        mock__setup_config_elements.assert_called_once()

    def test_ix_update_frame(self):
        static_traffic_params = {
            UPLINK: {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": {
                        "64B": "100",
                        "1KB": "0",
                    },
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            DOWNLINK: {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": False,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.remapIds.return_value = ["0"]
        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]
        self.ixnet.getList.side_effect = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_update_frame(static_traffic_params)
        self.assertIsNone(result)
        self.assertEqual(self.ixnet.setMultiAttribute.call_count, 7)
        self.assertEqual(self.ixnet.commit.call_count, 2)

    # NOTE(ralonsoh): to be updated in next patchset
    def test_update_ether_multi_attribute(self):
        pass

    # NOTE(ralonsoh): to be updated in next patchset
    def test_update_ether_multi_attributes(self):
        pass

    # NOTE(ralonsoh): to be updated in next patchset
    def test_update_ether(self):
        pass

    # NOTE(ralonsoh): to be updated in next patchset
    def test_ix_update_udp(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_update_udp({})
        self.assertIsNone(result)

    # NOTE(ralonsoh): to be updated in next patchset
    def test_ix_update_tcp(self):
        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_update_tcp({})
        self.assertIsNone(result)

    # NOTE(ralonsoh): to be updated in next patchset
    def test_ix_start_traffic(self):
        self.ixnet.getList.return_value = [0]
        self.ixnet.getAttribute.return_value = 'down'

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(self.ixnet.execute.call_count, 3)

    # NOTE(ralonsoh): to be updated in next patchset
    def test_ix_stop_traffic(self):
        self.ixnet.getList.return_value = [0]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_stop_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.ixnet.execute.assert_called_once()

    # NOTE(ralonsoh): to be updated in next patchset
    def test_build_stats_map(self):
        pass

    # NOTE(ralonsoh): to be updated in next patchset
    def test_get_statistics(self):
        self.ixnet.execute.return_value = ""

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.get_statistics()
        self.assertIsNotNone(result)
        self.assertEqual(self.ixnet.execute.call_count, 12)

    # NOTE(ralonsoh): to be updated in next patchset
    def test_add_ip_header_v4(self):
        static_traffic_params = {
            "uplink_0": {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "count": 1024,
                    "ttl": 32
                },
                "outer_l3v4": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            "downlink_0": {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.remapIds.return_value = ["0"]
        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]
        self.ixnet.getList.side_effect = [[1], [0], [0], ["srcIp", "dstIp"]]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_params,
                                         IxNet.IP_VERSION_4)
        self.assertIsNone(result)
        self.ixnet.setMultiAttribute.assert_called()
        self.ixnet.commit.assert_called_once()

    def test_add_ip_header_v4_nothing_to_do(self):
        static_traffic_params = {
            "uplink_0": {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "count": 1024,
                    "ttl": 32
                },
                "outer_l3v4": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            "downlink_0": {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.remapIds.return_value = ["0"]
        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]
        self.ixnet.getList.side_effect = [[1], [0, 1], [0], ["srcIp", "dstIp"]]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_params,
                                         IxNet.IP_VERSION_4)
        self.assertIsNone(result)
        self.ixnet.setMultiAttribute.assert_called()
        self.ixnet.commit.assert_called_once()

    def test_add_ip_header_v6(self):
        static_traffic_profile = {
            "uplink_0": {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            "downlink_0": {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.getList.side_effect = [[1], [1], [1], ["srcIp", "dstIp"]]
        self.ixnet.remapIds.return_value = ["0"]
        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_profile,
                                         IxNet.IP_VERSION_6)
        self.assertIsNone(result)
        self.ixnet.setMultiAttribute.assert_called()
        self.ixnet.commit.assert_called_once()

    def test_add_ip_header_v6_nothing_to_do(self):
        static_traffic_params = {
            "uplink_0": {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "count": 1024,
                    "ttl": 32
                },
                "outer_l3v6": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            "downlink_0": {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": True,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.getList.side_effect = [[1], [0, 1], [1], ["srcIP", "dstIP"]]
        self.ixnet.remapIds.return_value = ["0"]
        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_params,
                                         IxNet.IP_VERSION_6)
        self.assertIsNone(result)
        self.ixnet.setMultiAttribute.assert_not_called()

    def test_set_random_ip_multi_attributes_bad_ip_version(self):
        bad_ip_version = object()
        ixnet_gen = IxNet.IxNextgen(mock.Mock())
        with self.assertRaises(ValueError):
            ixnet_gen.set_random_ip_multi_attributes(
                mock.Mock(), bad_ip_version, mock.Mock(), mock.Mock())

    def test_get_config(self):
        tg_cfg = {
            "vdu": [
                {
                    "external-interface": [
                        {
                            "virtual-interface": {
                                "vpci": "0000:07:00.1",
                            },
                        },
                        {
                            "virtual-interface": {
                                "vpci": "0001:08:01.2",
                            },
                        },
                    ],
                },
            ],
            "mgmt-interface": {
                "ip": "test1",
                "tg-config": {
                    "dut_result_dir": "test2",
                    "version": "test3",
                    "ixchassis": "test4",
                    "tcl_port": "test5",
                },
            }
        }

        expected = {
            'machine': 'test1',
            'port': 'test5',
            'chassis': 'test4',
            'cards': ['0000', '0001'],
            'ports': ['07', '08'],
            'output_dir': 'test2',
            'version': 'test3',
            'bidir': True,
        }

        result = IxNet.IxNextgen.get_config(tg_cfg)
        self.assertEqual(result, expected)

    def test_ix_update_ether(self):
        static_traffic_params = {
            "uplink_0": {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": 64,
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            "downlink_0": {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": True,
                    "framesize": 64,
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]
        self.ixnet.getList.side_effect = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_update_ether(static_traffic_params)
        self.assertIsNone(result)
        self.ixnet.setMultiAttribute.assert_called()

    def test_ix_update_ether_nothing_to_do(self):
        static_traffic_params = {
            "uplink_0": {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            "downlink_0": {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]
        self.ixnet.getList.side_effect = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        ixnet_gen = IxNet.IxNextgen(self.ixnet)

        result = ixnet_gen.ix_update_ether(static_traffic_params)
        self.assertIsNone(result)
        self.ixnet.setMultiAttribute.assert_not_called()
