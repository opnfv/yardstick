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

import ipaddress

import mock
import six
import unittest

from yardstick.tests import STL_MOCKS
from yardstick.common import exceptions as y_exc

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.traffic_profile.base import TrafficProfile
    from yardstick.network_services.traffic_profile.trex_traffic_profile import TrexProfile
    from yardstick.network_services.traffic_profile.trex_traffic_profile import SRC
    from yardstick.network_services.traffic_profile.trex_traffic_profile import DST
    from yardstick.network_services.traffic_profile.trex_traffic_profile import ETHERNET
    from yardstick.network_services.traffic_profile.trex_traffic_profile import IP
    from yardstick.network_services.traffic_profile.trex_traffic_profile import IPv6
    from yardstick.network_services.traffic_profile.trex_traffic_profile import UDP
    from yardstick.network_services.traffic_profile.trex_traffic_profile import SRC_PORT
    from yardstick.network_services.traffic_profile.trex_traffic_profile import DST_PORT
    from yardstick.network_services.traffic_profile.trex_traffic_profile import TYPE_OF_SERVICE


class TestTrexProfile(unittest.TestCase):
    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64}}

    EXAMPLE_ETHERNET_ADDR = "00:00:00:00:00:01"
    EXAMPLE_IP_ADDR = "10.0.0.1"
    EXAMPLE_IPv6_ADDR = "0064:ff9b:0:0:0:0:9810:6414"

    PROFILE = {
        'description': 'Traffic profile to run RFC2544 latency',
        'name': 'rfc2544',
        'traffic_profile': {'traffic_type': 'RFC2544Profile',
                            'frame_rate': 100},
        TrafficProfile.DOWNLINK: {
            'ipv4': {'outer_l2': {'framesize': {'64B': '100',
                                                '1518B': '0',
                                                '128B': '0',
                                                '1400B': '0',
                                                '256B': '0',
                                                '373b': '0',
                                                '570B': '0'},
                                  "srcmac": "00:00:00:00:00:02",
                                  "dstmac": "00:00:00:00:00:01"},
                     'outer_l3v4': {'dstip4': '1.1.1.1-1.1.2.2',
                                    'proto': 'udp',
                                    'srcip4': '9.9.1.1-90.1.2.2',
                                    'dscp': 0, 'ttl': 32,
                                    'count': 1},
                     'outer_l4': {'srcport': '2001',
                                  'dsrport': '1234',
                                  'count': 1}}},
        TrafficProfile.UPLINK: {
            'ipv4':
                {'outer_l2': {'framesize':
                                  {'64B': '100', '1518B': '0',
                                   '128B': '0', '1400B': '0',
                                   '256B': '0', '373b': '0',
                                   '570B': '0'},
                              "srcmac": "00:00:00:00:00:01",
                              "dstmac": "00:00:00:00:00:02"},
                 'outer_l3v4': {'dstip4': '9.9.1.1-90.105.255.255',
                                'proto': 'udp',
                                'srcip4': '1.1.1.1-1.15.255.255',
                                'dscp': 0, 'ttl': 32, 'count': 1},
                 'outer_l4': {'dstport': '2001',
                              'srcport': '1234',
                              'count': 1}}},
        'schema': 'isb:traffic_profile:0.1'}
    PROFILE_v6 = {
        'description': 'Traffic profile to run RFC2544 latency',
        'name': 'rfc2544',
        'traffic_profile': {'traffic_type': 'RFC2544Profile',
                            'frame_rate': 100},
        TrafficProfile.DOWNLINK: {
            'ipv6': {'outer_l2': {'framesize':
                                      {'64B': '100', '1518B': '0',
                                       '128B': '0', '1400B': '0',
                                       '256B': '0', '373b': '0',
                                       '570B': '0'},
                                  "srcmac": "00:00:00:00:00:02",
                                  "dstmac": "00:00:00:00:00:01"},
                     'outer_l3v4': {
                         'dstip6':
                             '0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420',
                         'proto': 'udp',
                         'srcip6':
                             '0064:ff9b:0:0:0:0:9810:2814-0064:ff9b:0:0:0:0:9810:2820',
                         'dscp': 0, 'ttl': 32,
                         'count': 1},
                     'outer_l4': {'srcport': '2001',
                                  'dsrport': '1234',
                                  'count': 1}}},
        TrafficProfile.UPLINK: {
            'ipv6': {'outer_l2': {'framesize':
                                      {'64B': '100', '1518B': '0',
                                       '128B': '0', '1400B': '0',
                                       '256B': '0', '373b': '0',
                                       '570B': '0'},
                                  "srcmac": "00:00:00:00:00:01",
                                  "dstmac": "00:00:00:00:00:02"},
                     'outer_l3v4': {
                         'dstip6':
                             '0064:ff9b:0:0:0:0:9810:2814-0064:ff9b:0:0:0:0:9810:2820',
                         'proto': 'udp',
                         'srcip6':
                             '0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420',
                         'dscp': 0, 'ttl': 32,
                         'count': 1},
                     'outer_l4': {'dstport': '2001',
                                  'srcport': '1234',
                                  'count': 1}}},
        'schema': 'isb:traffic_profile:0.1'}

    def test___init__(self):
        TrafficProfile.params = self.PROFILE
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(trex_profile.pps, 100)

    def test_qinq(self):
        qinq = {"S-VLAN": {"id": 128, "priority": 0, "cfi": 0},
                "C-VLAN": {"id": 512, "priority": 0, "cfi": 0}}

        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertIsNone(trex_profile.set_qinq(qinq))

        qinq = {"S-VLAN": {"id": "128-130", "priority": 0, "cfi": 0},
                "C-VLAN": {"id": "512-515", "priority": 0, "cfi": 0}}
        self.assertIsNone(trex_profile.set_qinq(qinq))

    def test__set_outer_l2_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        qinq = {"S-VLAN": {"id": 128, "priority": 0, "cfi": 0},
                "C-VLAN": {"id": 512, "priority": 0, "cfi": 0}}
        outer_l2 = self.PROFILE[TrafficProfile.UPLINK]['ipv4']['outer_l2']
        outer_l2['QinQ'] = qinq
        self.assertIsNone(trex_profile._set_outer_l2_fields(outer_l2))

    def test__set_outer_l3v4_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        outer_l3v4 = self.PROFILE[TrafficProfile.UPLINK]['ipv4']['outer_l3v4']
        outer_l3v4['proto'] = 'tcp'
        self.assertIsNone(trex_profile._set_outer_l3v4_fields(outer_l3v4))

    def test__set_outer_l3v6_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        outer_l3v6 = self.PROFILE_v6[TrafficProfile.UPLINK]['ipv6']['outer_l3v4']
        outer_l3v6['proto'] = 'tcp'
        outer_l3v6['tc'] = 1
        outer_l3v6['hlim'] = 10
        self.assertIsNone(trex_profile._set_outer_l3v6_fields(outer_l3v6))

    def test__set_outer_l4_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        outer_l4 = self.PROFILE[TrafficProfile.UPLINK]['ipv4']['outer_l4']
        self.assertIsNone(trex_profile._set_outer_l4_fields(outer_l4))

    def test_get_streams(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        trex_profile.params = self.PROFILE
        profile_data = self.PROFILE[TrafficProfile.UPLINK]
        self.assertIsNotNone(trex_profile.get_streams(profile_data))
        trex_profile.pg_id = 1
        self.assertIsNotNone(trex_profile.get_streams(profile_data))
        trex_profile.params = self.PROFILE_v6
        trex_profile.profile_data = self.PROFILE_v6[TrafficProfile.UPLINK]
        self.assertIsNotNone(trex_profile.get_streams(profile_data))
        trex_profile.pg_id = 1
        self.assertIsNotNone(trex_profile.get_streams(profile_data))

    def test_generate_packets(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        trex_profile.fsize = 10
        trex_profile.base_pkt = [10]
        self.assertIsNone(trex_profile.generate_packets())

    def test_generate_imix_data_error(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual({}, trex_profile.generate_imix_data(False))

    def test__count_ip_ipv4(self):
        start, end, count = TrexProfile._count_ip('1.1.1.1', '1.2.3.4')
        self.assertEqual('1.1.1.1', str(start))
        self.assertEqual('1.2.3.4', str(end))
        diff = (int(ipaddress.IPv4Address(six.u('1.2.3.4'))) -
                int(ipaddress.IPv4Address(six.u('1.1.1.1'))))
        self.assertEqual(diff, count)

    def test__count_ip_ipv6(self):
        start_ip = '0064:ff9b:0:0:0:0:9810:6414'
        end_ip = '0064:ff9b:0:0:0:0:9810:6420'
        start, end, count = TrexProfile._count_ip(start_ip, end_ip)
        self.assertEqual(0x98106414, start)
        self.assertEqual(0x98106420, end)
        self.assertEqual(0x98106420 - 0x98106414, count)

    def test__count_ip_ipv6_exception(self):
        start_ip = '0064:ff9b:0:0:0:0:9810:6420'
        end_ip = '0064:ff9b:0:0:0:0:9810:6414'
        with self.assertRaises(y_exc.IPv6RangeError):
            TrexProfile._count_ip(start_ip, end_ip)

    def test__dscp_range_action_partial_actual_count_zero(self):
        traffic_profile = TrexProfile(TrafficProfile)
        dscp_partial = traffic_profile._dscp_range_action_partial()

        flow_vars_initial_length = len(traffic_profile.vm_flow_vars)
        dscp_partial('1', '1', 'unneeded')
        self.assertEqual(len(traffic_profile.vm_flow_vars), flow_vars_initial_length + 2)

    def test__dscp_range_action_partial_count_greater_than_actual(self):
        traffic_profile = TrexProfile(TrafficProfile)
        dscp_partial = traffic_profile._dscp_range_action_partial()

        flow_vars_initial_length = len(traffic_profile.vm_flow_vars)
        dscp_partial('1', '10', '100')
        self.assertEqual(len(traffic_profile.vm_flow_vars), flow_vars_initial_length + 2)

    def test__udp_range_action_partial_actual_count_zero(self):
        traffic_profile = TrexProfile(TrafficProfile)
        traffic_profile.udp['field1'] = 'value1'
        udp_partial = traffic_profile._udp_range_action_partial('field1')

        flow_vars_initial_length = len(traffic_profile.vm_flow_vars)
        udp_partial('1', '1', 'unneeded')
        self.assertEqual(len(traffic_profile.vm_flow_vars), flow_vars_initial_length + 2)

    def test__udp_range_action_partial_count_greater_than_actual(self):
        traffic_profile = TrexProfile(TrafficProfile)
        traffic_profile.udp['field1'] = 'value1'
        udp_partial = traffic_profile._udp_range_action_partial('field1', 'not_used_count')

        flow_vars_initial_length = len(traffic_profile.vm_flow_vars)
        udp_partial('1', '10', '100')
        self.assertEqual(len(traffic_profile.vm_flow_vars), flow_vars_initial_length + 2)

    def test__general_single_action_partial(self):
        trex_profile = TrexProfile(TrafficProfile)

        trex_profile._general_single_action_partial(ETHERNET)(SRC)(
            self.EXAMPLE_ETHERNET_ADDR)
        self.assertEqual(self.EXAMPLE_ETHERNET_ADDR,
                         trex_profile.ether_packet.src)

        trex_profile._general_single_action_partial(IP)(DST)(
            self.EXAMPLE_IP_ADDR)
        self.assertEqual(self.EXAMPLE_IP_ADDR, trex_profile.ip_packet.dst)

        trex_profile._general_single_action_partial(IPv6)(DST)(
            self.EXAMPLE_IPv6_ADDR)
        self.assertEqual(self.EXAMPLE_IPv6_ADDR, trex_profile.ip6_packet.dst)

        trex_profile._general_single_action_partial(UDP)(SRC_PORT)(5060)
        self.assertEqual(5060, trex_profile.udp_packet.sport)

        trex_profile._general_single_action_partial(IP)(TYPE_OF_SERVICE)(0)
        self.assertEqual(0, trex_profile.ip_packet.tos)

    def test__set_proto_addr(self):
        trex_profile = TrexProfile(TrafficProfile)

        ether_range = "00:00:00:00:00:01-00:00:00:00:00:02"
        ip_range = "1.1.1.2-1.1.1.10"
        ipv6_range = '0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420'

        trex_profile._set_proto_addr(ETHERNET, SRC, ether_range)
        trex_profile._set_proto_addr(ETHERNET, DST, ether_range)
        trex_profile._set_proto_addr(IP, SRC, ip_range)
        trex_profile._set_proto_addr(IP, DST, ip_range)
        trex_profile._set_proto_addr(IPv6, SRC, ipv6_range)
        trex_profile._set_proto_addr(IPv6, DST, ipv6_range)
        trex_profile._set_proto_addr(UDP, SRC_PORT, "5060-5090")
        trex_profile._set_proto_addr(UDP, DST_PORT, "5060")
