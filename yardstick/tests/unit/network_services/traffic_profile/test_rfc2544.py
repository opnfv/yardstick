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
            mock.call('profile1', rfc2544_profile.rate, mock.ANY),
            mock.call('profile1', rfc2544_profile.rate, mock.ANY),
            mock.call('profile2', rfc2544_profile.rate, mock.ANY),
            mock.call('profile2', rfc2544_profile.rate, mock.ANY)])
        mock_generator.client.add_streams.assert_has_calls([
            mock.call(mock.ANY, ports=[10]),
            mock.call(mock.ANY, ports=[20]),
            mock.call(mock.ANY, ports=[30]),
            mock.call(mock.ANY, ports=[40])])
        mock_generator.client.start(ports=[10, 20, 30, 40],
                                    duration=rfc2544_profile.config.duration,
                                    force=True)

    def test__create_imix_data(self):
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        data = {'64B': 50, '128B': 50}
        self.assertEqual({'64': 50.0, '128': 50.0},
                         rfc2544_profile._create_imix_data(data))
        data = {'64B': 1, '128b': 3}
        self.assertEqual({'64': 25.0, '128': 75.0},
                         rfc2544_profile._create_imix_data(data))
        data = {}
        self.assertEqual({}, rfc2544_profile._create_imix_data(data))

    def test__create_vm(self):
        packet = {'outer_l2': 'l2_definition'}
        rfc2544_profile = rfc2544.RFC2544Profile(self.TRAFFIC_PROFILE)
        with mock.patch.object(rfc2544_profile, '_set_outer_l2_fields') as \
                mock_l2_fileds:
            rfc2544_profile._create_vm(packet)
        mock_l2_fileds.assert_called_once_with('l2_definition')


# def _create_single_packet(self, size=64):
#     size -= 4
#     ether_packet = self.ether_packet
#     ip_packet = self.ip6_packet if self.ip6_packet else self.ip_packet
#     udp_packet = self.udp_packet
#     if self.qinq:
#         qinq_packet = self.qinq_packet
#         base_pkt = ether_packet / qinq_packet / ip_packet / udp_packet
#     else:
#         base_pkt = ether_packet / ip_packet / udp_packet
#     pad = max(0, size - len(base_pkt)) * 'x'
#     packet = trex_stl_packet_builder_scapy.STLPktBuilder(
#         pkt=base_pkt / pad, vm=self.trex_vm)
#     return packet

    def test__create_single_packet(self):
        pass


#
# def _create_streams(self, imix_data, rate, port_pg_id):
#     """Create a list of streams per packet size
#
#     The STL TX mode speed of the generated streams will depend on the frame
#     weight and the frame rate. Both the frame weight and the total frame
#     rate are normalized to 100. The STL TX mode speed, defined in
#     percentage, is the combitation of both percentages. E.g.:
#       frame weight = 100
#       rate = 90
#         --> STLTXmode percentage = 10 (%)
#
#       frame weight = 80
#       rate = 50
#         --> STLTXmode percentage = 40 (%)
#
#     :param imix_data: (dict) IMIX size and weight
#     :param rate: (float) normalized [0..100] total weight
#     :param pg_id: (PortPgIDMap) port / pg_id (list) map
#     """
#     streams = []
#     for size, weight in ((int(size), float(weight)) for (size, weight)
#                          in imix_data.items() if float(weight) > 0):
#         packet = self._create_single_packet(size)
#         pg_id = port_pg_id.increase_pg_id()
#         stl_flow = trex_stl_streams.STLFlowLatencyStats(pg_id=pg_id)
#         mode = trex_stl_streams.STLTXCont(
#             percentage=weight * rate / 100)
#         streams.append(trex_stl_client.STLStream(
#             packet=packet, flow_stats=stl_flow, mode=mode))
#     return streams

    def test__create_streams(self):
        pass

# def get_drop_percentage(self, samples, tolerance_low, tolerance_high,
#                         correlated_traffic):
#     """Calculate the drop percentage and run the traffic"""
#     tx_rate_fps = 0
#     rx_rate_fps = 0
#     for sample in samples:
#         tx_rate_fps += sum(
#             port['tx_throughput_fps'] for port in sample.values())
#         rx_rate_fps += sum(
#             port['rx_throughput_fps'] for port in sample.values())
#     tx_rate_fps /= len(samples)
#     rx_rate_fps /= len(samples)
#
#     # TODO(esm): RFC2544 doesn't tolerate packet loss, why do we?
#     out_packets = sum(
#         port['out_packets'] for port in samples[-1].values())
#     in_packets = sum(
#         port['in_packets'] for port in samples[-1].values())
#     drop_percent = 100.0
#
#     # https://tools.ietf.org/html/rfc2544#section-26.3
#     if out_packets:
#         drop_percent = round(
#             (float(abs(out_packets - in_packets)) / out_packets) * 100,
#             5)
#
#     if drop_percent > tolerance_high:
#         self.max_rate = self.rate
#     elif drop_percent < tolerance_low:
#         self.min_rate = self.rate
#     last_rate = self.rate
#     self.rate = round(float(self.max_rate + self.min_rate) / 2.0, 5)
#
#     throughput = rx_rate_fps * 2 if correlated_traffic else rx_rate_fps
#
#     if drop_percent > self.drop_percent_max:
#         self.drop_percent_max = drop_percent
#
#     latency = {port_num: value['latency']
#                for port_num, value in samples[-1].items()}
#
#     output = {
#         'TxThroughput': tx_rate_fps,
#         'RxThroughput': rx_rate_fps,
#         'CurrentDropPercentage': drop_percent,
#         'Throughput': throughput,
#         'DropPercentage': self.drop_percent_max,
#         'Rate': last_rate,
#         'Latency': latency
#     }
#     return output

    def test_get_drop_percentage(self):
        pass






class PortPgIDMapTestCase(base.BaseUnitTestCase):

    def test_add_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        self.assertEqual(10, port_pg_id_map._last_port)
        self.assertEqual([], port_pg_id_map._port_pg_id_map[10])

    def test_get_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        port_pg_id_map.increase_pg_id()
        port_pg_id_map.increase_pg_id()
        port_pg_id_map.add_port(20)
        port_pg_id_map.increase_pg_id()
        self.assertEqual([1, 2], port_pg_id_map.get_port(10))
        self.assertEqual([3], port_pg_id_map.get_port(20))

    def test_increase_pg_id_no_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        self.assertIsNone(port_pg_id_map.increase_pg_id())

    def test_increase_pg_id_last_port(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        self.assertEqual(1, port_pg_id_map.increase_pg_id())
        self.assertEqual([1], port_pg_id_map.get_port(10))
        self.assertEqual(10, port_pg_id_map._last_port)

    def test_increase_pg_id(self):
        port_pg_id_map = rfc2544.PortPgIDMap()
        port_pg_id_map.add_port(10)
        port_pg_id_map.increase_pg_id()
        self.assertEqual(2, port_pg_id_map.increase_pg_id(port=20))
        self.assertEqual([1], port_pg_id_map.get_port(10))
        self.assertEqual([2], port_pg_id_map.get_port(20))
        self.assertEqual(20, port_pg_id_map._last_port)
