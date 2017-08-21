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

STL_MOCKS = {
    'stl': mock.MagicMock(),
    'stl.trex_stl_lib': mock.MagicMock(),
    'stl.trex_stl_lib.base64': mock.MagicMock(),
    'stl.trex_stl_lib.binascii': mock.MagicMock(),
    'stl.trex_stl_lib.collections': mock.MagicMock(),
    'stl.trex_stl_lib.copy': mock.MagicMock(),
    'stl.trex_stl_lib.datetime': mock.MagicMock(),
    'stl.trex_stl_lib.functools': mock.MagicMock(),
    'stl.trex_stl_lib.imp': mock.MagicMock(),
    'stl.trex_stl_lib.inspect': mock.MagicMock(),
    'stl.trex_stl_lib.json': mock.MagicMock(),
    'stl.trex_stl_lib.linecache': mock.MagicMock(),
    'stl.trex_stl_lib.math': mock.MagicMock(),
    'stl.trex_stl_lib.os': mock.MagicMock(),
    'stl.trex_stl_lib.platform': mock.MagicMock(),
    'stl.trex_stl_lib.pprint': mock.MagicMock(),
    'stl.trex_stl_lib.random': mock.MagicMock(),
    'stl.trex_stl_lib.re': mock.MagicMock(),
    'stl.trex_stl_lib.scapy': mock.MagicMock(),
    'stl.trex_stl_lib.socket': mock.MagicMock(),
    'stl.trex_stl_lib.string': mock.MagicMock(),
    'stl.trex_stl_lib.struct': mock.MagicMock(),
    'stl.trex_stl_lib.sys': mock.MagicMock(),
    'stl.trex_stl_lib.threading': mock.MagicMock(),
    'stl.trex_stl_lib.time': mock.MagicMock(),
    'stl.trex_stl_lib.traceback': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_async_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_exceptions': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_ext': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_jsonrpc_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_interface': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_scapy': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_port': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_stats': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_streams': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_types': mock.MagicMock(),
    'stl.trex_stl_lib.types': mock.MagicMock(),
    'stl.trex_stl_lib.utils': mock.MagicMock(),
    'stl.trex_stl_lib.utils.argparse': mock.MagicMock(),
    'stl.trex_stl_lib.utils.collections': mock.MagicMock(),
    'stl.trex_stl_lib.utils.common': mock.MagicMock(),
    'stl.trex_stl_lib.utils.json': mock.MagicMock(),
    'stl.trex_stl_lib.utils.os': mock.MagicMock(),
    'stl.trex_stl_lib.utils.parsing_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.pwd': mock.MagicMock(),
    'stl.trex_stl_lib.utils.random': mock.MagicMock(),
    'stl.trex_stl_lib.utils.re': mock.MagicMock(),
    'stl.trex_stl_lib.utils.string': mock.MagicMock(),
    'stl.trex_stl_lib.utils.sys': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_tables': mock.MagicMock(),
    'stl.trex_stl_lib.utils.texttable': mock.MagicMock(),
    'stl.trex_stl_lib.warnings': mock.MagicMock(),
    'stl.trex_stl_lib.yaml': mock.MagicMock(),
    'stl.trex_stl_lib.zlib': mock.MagicMock(),
    'stl.trex_stl_lib.zmq': mock.MagicMock(),
}

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.traffic_profile.base import TrafficProfile
    from yardstick.network_services.traffic_profile.traffic_profile import \
        TrexProfile


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

    PROFILE = {'description': 'Traffic profile to run RFC2544 latency',
               'name': 'rfc2544',
               'traffic_profile': {'traffic_type': 'RFC2544Profile',
                                   'frame_rate': 100},
               'public': {'ipv4': {'outer_l2': {'framesize': {'64B': '100',
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
                                                  'dscp': 0, 'ttl': 32},
                                   'outer_l4': {'srcport': '2001',
                                                'dsrport': '1234'}}},
               'private': {'ipv4':
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
                                           'dscp': 0, 'ttl': 32},
                            'outer_l4': {'dstport': '2001',
                                         'srcport': '1234'}}},
               'schema': 'isb:traffic_profile:0.1'}
    PROFILE_v6 = {'description': 'Traffic profile to run RFC2544 latency',
                  'name': 'rfc2544',
                  'traffic_profile': {'traffic_type': 'RFC2544Profile',
                                      'frame_rate': 100},
                  'public': {'ipv6': {'outer_l2': {'framesize':
                                                   {'64B': '100', '1518B': '0',
                                                    '128B': '0', '1400B': '0',
                                                    '256B': '0', '373b': '0',
                                                    '570B': '0'},
                                                   "srcmac": "00:00:00:00:00:02",
                                                   "dstmac": "00:00:00:00:00:01"},
                                      'outer_l3v4': {'dstip6': '0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420',
                                                     'proto': 'udp',
                                                     'srcip6': '0064:ff9b:0:0:0:0:9810:2814-0064:ff9b:0:0:0:0:9810:2820',
                                                     'dscp': 0, 'ttl': 32},
                                      'outer_l4': {'srcport': '2001',
                                                   'dsrport': '1234'}}},
                  'private':
                  {'ipv6': {'outer_l2': {'framesize':
                                         {'64B': '100', '1518B': '0',
                                          '128B': '0', '1400B': '0',
                                          '256B': '0', '373b': '0',
                                          '570B': '0'},
                                         "srcmac": "00:00:00:00:00:01",
                                         "dstmac": "00:00:00:00:00:02"},
                            'outer_l3v4': {'dstip6': '0064:ff9b:0:0:0:0:9810:2814-0064:ff9b:0:0:0:0:9810:2820',
                                           'proto': 'udp',
                                           'srcip6': '0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420',
                                           'dscp': 0, 'ttl': 32},
                            'outer_l4': {'dstport': '2001',
                                         'srcport': '1234'}}},
                  'schema': 'isb:traffic_profile:0.1'}

    def test___init__(self):
        TrafficProfile.params = self.PROFILE
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(trex_profile.pps, 100)

    def test_execute(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.execute({}))

    def test_set_src_mac(self):
        src_mac = "00:00:00:00:00:01"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_src_mac(src_mac))

        src_mac = "00:00:00:00:00:01-00:00:00:00:00:02"
        self.assertEqual(None, trex_profile.set_src_mac(src_mac))

    def test_set_dst_mac(self):
        dst_mac = "00:00:00:00:00:03"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_dst_mac(dst_mac))

        dst_mac = "00:00:00:00:00:03-00:00:00:00:00:04"
        self.assertEqual(None, trex_profile.set_dst_mac(dst_mac))

    def test_set_src_ip4(self):
        src_ipv4 = "152.16.100.20"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_src_ip4(src_ipv4))

        src_ipv4 = "152.16.100.20-152.16.100.30"
        self.assertEqual(None, trex_profile.set_src_ip4(src_ipv4))

    def test_set_dst_ip4(self):
        dst_ipv4 = "152.16.100.20"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_dst_ip4(dst_ipv4))

        dst_ipv4 = "152.16.100.20-152.16.100.30"
        self.assertEqual(None, trex_profile.set_dst_ip4(dst_ipv4))

    def test_set_src_ip6(self):
        src_ipv6 = "0064:ff9b:0:0:0:0:9810:6414"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_src_ip6(src_ipv6))

        src_ipv6 = "0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420"
        self.assertEqual(None, trex_profile.set_src_ip6(src_ipv6))

    def test_set_dst_ip6(self):
        dst_ipv6 = "0064:ff9b:0:0:0:0:9810:6414"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_dst_ip6(dst_ipv6))

        dst_ipv6 = "0064:ff9b:0:0:0:0:9810:6414-0064:ff9b:0:0:0:0:9810:6420"
        self.assertEqual(None, trex_profile.set_dst_ip6(dst_ipv6))

    def test_dscp(self):
        dscp = "0"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_dscp(dscp))

        dscp = "0-1"
        self.assertEqual(None, trex_profile.set_dscp(dscp))

    def test_src_port(self):
        port = "1234"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_src_port(port))

        port = "1234-5678"
        self.assertEqual(None, trex_profile.set_src_port(port))

    def test_dst_port(self):
        port = "1234"
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_dst_port(port))

        port = "1234-5678"
        self.assertEqual(None, trex_profile.set_dst_port(port))

    def test_qinq(self):
        qinq = {"S-VLAN": {"id": 128, "priority": 0, "cfi": 0},
                "C-VLAN": {"id": 512, "priority": 0, "cfi": 0}}

        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertEqual(None, trex_profile.set_qinq(qinq))

        qinq = {"S-VLAN": {"id": "128-130", "priority": 0, "cfi": 0},
                "C-VLAN": {"id": "512-515", "priority": 0, "cfi": 0}}
        self.assertEqual(None, trex_profile.set_qinq(qinq))

    def test_set_outer_l2_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        qinq = {"S-VLAN": {"id": 128, "priority": 0, "cfi": 0},
                "C-VLAN": {"id": 512, "priority": 0, "cfi": 0}}
        outer_l2 = self.PROFILE['private']['ipv4']['outer_l2']
        outer_l2['QinQ'] = qinq
        self.assertEqual(None, trex_profile.set_outer_l2_fields(outer_l2))

    def test_set_outer_l3v4_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        outer_l3v4 = self.PROFILE['private']['ipv4']['outer_l3v4']
        outer_l3v4['proto'] = 'tcp'
        self.assertEqual(None, trex_profile.set_outer_l3v4_fields(outer_l3v4))

    def test_set_outer_l3v6_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        outer_l3v6 = self.PROFILE_v6['private']['ipv6']['outer_l3v4']
        outer_l3v6['proto'] = 'tcp'
        outer_l3v6['tc'] = 1
        outer_l3v6['hlim'] = 10
        self.assertEqual(None, trex_profile.set_outer_l3v6_fields(outer_l3v6))

    def test_set_outer_l4_fields(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        outer_l4 = self.PROFILE['private']['ipv4']['outer_l4']
        self.assertEqual(None, trex_profile.set_outer_l4_fields(outer_l4))

    def test_get_streams(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        trex_profile.params = self.PROFILE
        profile_data = self.PROFILE["private"]
        self.assertIsNotNone(trex_profile.get_streams(profile_data))
        trex_profile.pg_id = 1
        self.assertIsNotNone(trex_profile.get_streams(profile_data))
        trex_profile.params = self.PROFILE_v6
        trex_profile.profile_data = self.PROFILE_v6["private"]
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

    def test__get_start_end_ipv6(self):
        trex_profile = \
            TrexProfile(TrafficProfile)
        self.assertRaises(SystemExit, trex_profile._get_start_end_ipv6,
                          "1.1.1.3", "1.1.1.1")
