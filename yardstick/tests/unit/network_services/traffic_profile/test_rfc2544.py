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

import datetime

import mock
from trex_stl_lib import api as Pkt
from trex_stl_lib import trex_stl_client
from trex_stl_lib import trex_stl_packet_builder_scapy
from trex_stl_lib import trex_stl_streams

from yardstick.common import constants
from yardstick.network_services.traffic_profile import rfc2544
from yardstick.tests.unit import base


class TestRFC2544Profile(base.BaseUnitTestCase):
    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,
            "flow_number": 10,
            "frame_size": 64}}

    PROFILE = {'description': 'Traffic profile to run RFC2544 latency',
               'name': 'rfc2544',
               'traffic_profile': {'traffic_type': 'RFC2544Profile',
                                   'frame_rate': 100},
               'downlink_0':
                   {'ipv4':
                        {'outer_l2':
                             {'framesize':
                                  {'64B': '100', '1518B': '0',
                                   '128B': '0', '1400B': '0',
                                   '256B': '0', '373b': '0',
                                   '570B': '0'}},
                         'outer_l3v4':
                             {'dstip4': '1.1.1.1-1.15.255.255',
                              'proto': 'udp',
                              'srcip4': '90.90.1.1-90.105.255.255',
                              'dscp': 0, 'ttl': 32, 'count': 1},
                         'outer_l4':
                             {'srcport': '2001',
                              'dsrport': '1234', 'count': 1}}},
               'uplink_0':
                   {'ipv4':
                        {'outer_l2':
                             {'framesize':
                                  {'64B': '100', '1518B': '0',
                                   '128B': '0', '1400B': '0',
                                   '256B': '0', '373b': '0',
                                   '570B': '0'}},
                         'outer_l3v4':
                             {'dstip4': '9.9.1.1-90.105.255.255',
                              'proto': 'udp',
                              'srcip4': '1.1.1.1-1.15.255.255',
                              'dscp': 0, 'ttl': 32, 'count': 1},
                         'outer_l4':
                             {'dstport': '2001',
                              'srcport': '1234', 'count': 1}}},
               'schema': 'isb:traffic_profile:0.1'}

    def test___init__(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        self.assertEqual(rfc2544_profile.max_rate, rfc2544_profile.rate)
        self.assertEqual(0, rfc2544_profile.min_rate)

    def test_stop_traffic(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        mock_generator = mock.Mock()
        rfc2544_profile.stop_traffic(traffic_generator=mock_generator)
        mock_generator.client.stop.assert_called_once()
        mock_generator.client.reset.assert_called_once()
        mock_generator.client.remove_all_streams.assert_called_once()

    def test_execute_traffic(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        mock_generator = mock.Mock()
        mock_generator.networks = {
            'downlink_0': ['xe0', 'xe1'],
            'uplink_0': ['xe2', 'xe3'],
            'downlink_1': []}
        mock_generator.port_num.side_effect = [10, 20, 30, 40]
        mock_generator.rfc2544_helper.correlated_traffic = False
        rfc2544_profile.params = {
            'downlink_0': 'profile1',
            'uplink_0': 'profile2'}

        with mock.patch.object(rfc2544_profile, '_create_profile') as \
                mock_create_profile:
            rfc2544_profile.execute_traffic(traffic_generator=mock_generator)
        mock_create_profile.assert_has_calls([
            mock.call('profile1', rfc2544_profile.rate, mock.ANY, False),
            mock.call('profile1', rfc2544_profile.rate, mock.ANY, False),
            mock.call('profile2', rfc2544_profile.rate, mock.ANY, False),
            mock.call('profile2', rfc2544_profile.rate, mock.ANY, False)])
        mock_generator.client.add_streams.assert_has_calls([
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[30]),
            mock.call(mock.ANY, ports=[40])])
        mock_generator.client.start(ports=[10, 20, 30, 40],
                                    duration=rfc2544_profile.config.duration,
                                    force=True)

    @mock.patch.object(trex_stl_streams, 'STLProfile')
    def test__create_profile(self, mock_stl_profile):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        port_pg_id = mock.ANY
        profile_data = {'packetid_1': {'outer_l2': {'framesize': 'imix_info'}}}
        rate = 100
        with mock.patch.object(rfc2544_profile, '_create_imix_data') as \
                mock_create_imix, \
                mock.patch.object(rfc2544_profile, '_create_vm') as \
                mock_create_vm, \
                mock.patch.object(rfc2544_profile, '_create_streams') as \
                mock_create_streams:
            mock_create_imix.return_value = 'imix_data'
            mock_create_streams.return_value = ['stream1']
            rfc2544_profile._create_profile(profile_data, rate, port_pg_id,
                                            True)

        mock_create_imix.assert_called_once_with('imix_info')
        mock_create_vm.assert_called_once_with(
            {'outer_l2': {'framesize': 'imix_info'}})
        mock_create_streams.assert_called_once_with('imix_data', 100,
                                                    port_pg_id, True)
        mock_stl_profile.assert_called_once_with(['stream1'])

    def test__create_imix_data_mode_DIB(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        data = {'64B': 50, '128B': 50}
        self.assertEqual(
            {'64': 50.0, '128': 50.0},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_BYTES))
        data = {'64B': 1, '128b': 3}
        self.assertEqual(
            {'64': 25.0, '128': 75.0},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_BYTES))
        data = {}
        self.assertEqual(
            {},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_BYTES))

    def test__create_imix_data_mode_DIP(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        data = {'64B': 25, '128B': 25, '512B': 25, '1518B': 25}
        byte_total = 64 * 25 + 128 * 25 + 512 * 25 + 1518 * 25
        self.assertEqual(
            {'64': 64 * 25.0 * 100 / byte_total,
             '128': 128 * 25.0 * 100 / byte_total,
             '512': 512 * 25.0 * 100 / byte_total,
             '1518': 1518 * 25.0 * 100/ byte_total},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_PACKETS))
        data = {}
        self.assertEqual(
            {},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_PACKETS))
        data = {'64B': 100}
        self.assertEqual(
            {'64': 100},
            rfc2544_profile._create_imix_data(
                data, weight_mode=constants.DISTRIBUTION_IN_PACKETS))

    def test__create_vm(self):
        packet = {'outer_l2': 'l2_definition'}
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        with mock.patch.object(rfc2544_profile, '_set_outer_l2_fields') as \
                mock_l2_fileds:
            rfc2544_profile._create_vm(packet)
        mock_l2_fileds.assert_called_once_with('l2_definition')

    @mock.patch.object(trex_stl_packet_builder_scapy, 'STLPktBuilder',
                       return_value='packet')
    def test__create_single_packet(self, mock_pktbuilder):
        size = 128
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.ether_packet = Pkt.Eth()
        rfc2544_profile.ip_packet = Pkt.IP()
        rfc2544_profile.udp_packet = Pkt.UDP()
        rfc2544_profile.trex_vm = 'trex_vm'
        base_pkt = (rfc2544_profile.ether_packet / rfc2544_profile.ip_packet /
                    rfc2544_profile.udp_packet)
        pad = (size - len(base_pkt)) * 'x'
        output = rfc2544_profile._create_single_packet(size=size)
        mock_pktbuilder.assert_called_once_with(pkt=base_pkt / pad,
                                                vm='trex_vm')
        self.assertEqual(output, 'packet')

    @mock.patch.object(trex_stl_packet_builder_scapy, 'STLPktBuilder',
                       return_value='packet')
    def test__create_single_packet_qinq(self, mock_pktbuilder):
        size = 128
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.ether_packet = Pkt.Eth()
        rfc2544_profile.ip_packet = Pkt.IP()
        rfc2544_profile.udp_packet = Pkt.UDP()
        rfc2544_profile.trex_vm = 'trex_vm'
        rfc2544_profile.qinq = True
        rfc2544_profile.qinq_packet = Pkt.Dot1Q(vlan=1) / Pkt.Dot1Q(vlan=2)
        base_pkt = (rfc2544_profile.ether_packet /
                    rfc2544_profile.qinq_packet / rfc2544_profile.ip_packet /
                    rfc2544_profile.udp_packet)
        pad = (size - len(base_pkt)) * 'x'
        output = rfc2544_profile._create_single_packet(size=size)
        mock_pktbuilder.assert_called_once_with(pkt=base_pkt / pad,
                                                vm='trex_vm')
        self.assertEqual(output, 'packet')

    @mock.patch.object(trex_stl_streams, 'STLFlowLatencyStats')
    @mock.patch.object(trex_stl_streams, 'STLTXCont')
    @mock.patch.object(trex_stl_client, 'STLStream')
    def test__create_streams(self, mock_stream, mock_txcont, mock_latency):
        imix_data = {'64': 25, '512': 75}
        rate = 35
        port_pg_id = rfc2544.PortPgIDMap()
        port_pg_id.add_port(10)
        mock_stream.side_effect = ['stream1', 'stream2']
        mock_txcont.side_effect = ['txcont1', 'txcont2']
        mock_latency.side_effect = ['latency1', 'latency2']
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        with mock.patch.object(rfc2544_profile, '_create_single_packet'):
            output = rfc2544_profile._create_streams(imix_data, rate,
                                                     port_pg_id, True)
        self.assertEqual(['stream1', 'stream2'], output)
        mock_latency.assert_has_calls([
            mock.call(pg_id=1), mock.call(pg_id=2)])
        mock_txcont.assert_has_calls([
            mock.call(percentage=float(25 * 35) / 100),
            mock.call(percentage=float(75 * 35) / 100)], any_order=True)

    def test_get_drop_percentage(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        samples = [
            {'xe1': {'tx_throughput_fps': 110,
                     'rx_throughput_fps': 101,
                     'out_packets': 2100,
                     'in_packets': 2010,
                     'timestamp': datetime.datetime(2000, 1, 1, 1, 1, 1, 1)},
             'xe2': {'tx_throughput_fps': 210,
                     'rx_throughput_fps': 201,
                     'out_packets': 4100,
                     'in_packets': 4010,
                     'timestamp': datetime.datetime(2000, 1, 1, 1, 1, 1, 1)}},
            {'xe1': {'tx_throughput_fps': 156,
                     'rx_throughput_fps': 108,
                     'out_packets': 2110,
                     'in_packets': 2040,
                     'latency': 'Latency1',
                     'timestamp': datetime.datetime(2000, 1, 1, 1, 1, 1, 31)},
             'xe2': {'tx_throughput_fps': 253,
                     'rx_throughput_fps': 215,
                     'out_packets': 4150,
                     'in_packets': 4010,
                     'latency': 'Latency2',
                     'timestamp': datetime.datetime(2000, 1, 1, 1, 1, 1, 31)}}
        ]
        completed, output = rfc2544_profile.get_drop_percentage(
            samples, 0, 0, False)
        expected = {'DropPercentage': 50.0,
                    'Latency': {'xe1': 'Latency1', 'xe2': 'Latency2'},
                    'RxThroughput': 1000000.0,
                    'TxThroughput': 2000000.0,
                    'CurrentDropPercentage': 50.0,
                    'Rate': 100.0,
                    'Throughput': 1000000.0}
        self.assertEqual(expected, output)
        self.assertFalse(completed)


class PortPgIDMapTestCase(base.BaseUnitTestCase):

    def test_add_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        self.assertEqual(10, port_pg_id_map._last_port)
        self.assertEqual([], port_pg_id_map._port_pg_id_map[10])

    def test_get_pg_ids(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        port_pg_id_map.increase_pg_id()
        port_pg_id_map.increase_pg_id()
        port_pg_id_map.add_port(20)
        port_pg_id_map.increase_pg_id()
        self.assertEqual([1, 2], port_pg_id_map.get_pg_ids(10))
        self.assertEqual([3], port_pg_id_map.get_pg_ids(20))
        self.assertEqual([], port_pg_id_map.get_pg_ids(30))

    def test_increase_pg_id_no_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        self.assertIsNone(port_pg_id_map.increase_pg_id())

    def test_increase_pg_id_last_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        self.assertEqual(1, port_pg_id_map.increase_pg_id())
        self.assertEqual([1], port_pg_id_map.get_pg_ids(10))
        self.assertEqual(10, port_pg_id_map._last_port)

    def test_increase_pg_id(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        port_pg_id_map.increase_pg_id()
        self.assertEqual(2, port_pg_id_map.increase_pg_id(port=20))
        self.assertEqual([1], port_pg_id_map.get_pg_ids(10))
        self.assertEqual([2], port_pg_id_map.get_pg_ids(20))
        self.assertEqual(20, port_pg_id_map._last_port)
