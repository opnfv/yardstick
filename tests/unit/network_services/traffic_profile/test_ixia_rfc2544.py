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
from __future__ import division
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
    from yardstick.network_services.traffic_profile.traffic_profile \
        import TrexProfile
    from yardstick.network_services.traffic_profile.ixia_rfc2544 import \
        IXIARFC2544Profile
    from yardstick.network_services.traffic_profile import ixia_rfc2544


class TestIXIARFC2544Profile(unittest.TestCase):
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
               'traffic_profile': {'traffic_type': 'IXIARFC2544Profile',
                                   'frame_rate': 100},
               'public': {'ipv4':
                          {'outer_l2': {'framesize':
                                        {'64B': '100', '1518B': '0',
                                         '128B': '0', '1400B': '0',
                                         '256B': '0', '373b': '0',
                                         '570B': '0'}},
                           'outer_l3v4': {'dstip4': '1.1.1.1-1.15.255.255',
                                          'proto': 'udp',
                                          'srcip4': '90.90.1.1-90.105.255.255',
                                          'dscp': 0, 'ttl': 32},
                           'outer_l4': {'srcport': '2001',
                                        'dsrport': '1234'}}},
               'private': {'ipv4':
                           {'outer_l2': {'framesize':
                                         {'64B': '100', '1518B': '0',
                                          '128B': '0', '1400B': '0',
                                          '256B': '0', '373b': '0',
                                          '570B': '0'}},
                            'outer_l3v4': {'dstip4': '9.9.1.1-90.105.255.255',
                                           'proto': 'udp',
                                           'srcip4': '1.1.1.1-1.15.255.255',
                                           'dscp': 0, 'ttl': 32},
                            'outer_l4': {'dstport': '2001',
                                         'srcport': '1234'}}},
               'schema': 'isb:traffic_profile:0.1'}

    def test_get_ixia_traffic_profile_error(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [-1]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        STATIC_TRAFFIC = {
            "private": {
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
            "public": {
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
        ixia_rfc2544.STATIC_TRAFFIC = STATIC_TRAFFIC

        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        mac = {"src_mac_0": "00:00:00:00:00:01",
               "src_mac_1": "00:00:00:00:00:02",
               "src_mac_2": "00:00:00:00:00:02",
               "dst_mac_0": "00:00:00:00:00:03",
               "dst_mac_1": "00:00:00:00:00:04",
               "dst_mac_2": "00:00:00:00:00:04"}
        self.assertRaises(IOError, r_f_c2544_profile._get_ixia_traffic_profile,
                          self.PROFILE, mac, xfile="tmp",
                          static_traffic=STATIC_TRAFFIC)


    @mock.patch("yardstick.network_services.traffic_profile.ixia_rfc2544.open")
    def test_get_ixia_traffic_profile(self, mock_open):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [-1]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        STATIC_TRAFFIC = {
            "private": {
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
            "public": {
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
        ixia_rfc2544.STATIC_TRAFFIC = STATIC_TRAFFIC

        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        mac = {"src_mac_0": "00:00:00:00:00:01",
               "src_mac_1": "00:00:00:00:00:02",
               "src_mac_2": "00:00:00:00:00:02",
               "dst_mac_0": "00:00:00:00:00:03",
               "dst_mac_1": "00:00:00:00:00:04",
               "dst_mac_2": "00:00:00:00:00:04"}
        result = r_f_c2544_profile._get_ixia_traffic_profile(
            self.PROFILE, mac, xfile="tmp", static_traffic=STATIC_TRAFFIC)
        self.assertIsNotNone(result)

    @mock.patch("yardstick.network_services.traffic_profile.ixia_rfc2544.open")
    def test_get_ixia_traffic_profile_v6(self, mock_open):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [-1]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        STATIC_TRAFFIC = {
            "private": {
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
            "public": {
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
        ixia_rfc2544.STATIC_TRAFFIC = STATIC_TRAFFIC

        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        mac = {"src_mac_0": "00:00:00:00:00:01",
               "src_mac_1": "00:00:00:00:00:02",
               "src_mac_2": "00:00:00:00:00:02",
               "dst_mac_0": "00:00:00:00:00:03",
               "dst_mac_1": "00:00:00:00:00:04",
               "dst_mac_2": "00:00:00:00:00:04"}
        profile_data = {'description': 'Traffic profile to run RFC2544',
                        'name': 'rfc2544',
                        'traffic_profile':
                        {'traffic_type': 'IXIARFC2544Profile',
                         'frame_rate': 100},
                        'public':
                        {'ipv4':
                         {'outer_l2': {'framesize':
                                       {'64B': '100', '1518B': '0',
                                        '128B': '0', '1400B': '0',
                                        '256B': '0', '373b': '0',
                                        '570B': '0'}},
                          'outer_l3v6': {'dstip6': '1.1.1.1-1.15.255.255',
                                         'proto': 'udp',
                                         'srcip6': '90.90.1.1-90.105.255.255',
                                         'dscp': 0, 'ttl': 32},
                          'outer_l4': {'srcport': '2001',
                                       'dsrport': '1234'}}},
                        'private': {'ipv4':
                                    {'outer_l2': {'framesize':
                                                  {'64B': '100', '1518B': '0',
                                                   '128B': '0', '1400B': '0',
                                                   '256B': '0', '373b': '0',
                                                   '570B': '0'}},
                                     'outer_l3v6':
                                     {'dstip6': '9.9.1.1-90.105.255.255',
                                      'proto': 'udp',
                                      'srcip6': '1.1.1.1-1.15.255.255',
                                      'dscp': 0, 'ttl': 32},
                                     'outer_l4': {'dstport': '2001',
                                                  'srcport': '1234'}}},
                        'schema': 'isb:traffic_profile:0.1'}
        result = r_f_c2544_profile._get_ixia_traffic_profile(
            profile_data, mac, static_traffic=STATIC_TRAFFIC)
        self.assertIsNotNone(result)

    def test__ixia_traffic_generate(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [-1]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        traffic = {"public": {'iload': 10},
                   "private": {'iload': 10}}
        ixia_obj = mock.MagicMock()
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        result = r_f_c2544_profile._ixia_traffic_generate(traffic_generator,
                                                          traffic, ixia_obj)
        self.assertIsNone(result)

    def test_execute(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [-1]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.first_run = True
        r_f_c2544_profile.params = {"public": {'iload': 10},
                                    "private": {'iload': 10}}

        r_f_c2544_profile.get_streams = mock.Mock()
        r_f_c2544_profile.full_profile = {}
        r_f_c2544_profile._get_ixia_traffic_profile = mock.Mock()
        r_f_c2544_profile.get_multiplier = mock.Mock()
        r_f_c2544_profile._ixia_traffic_generate = mock.Mock()
        ixia_obj = mock.MagicMock()
        self.assertEqual(None, r_f_c2544_profile.execute(traffic_generator,
                                                         ixia_obj))

    def test_get_drop_percentage(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        ixia_obj = mock.MagicMock()
        r_f_c2544_profile.execute = mock.Mock()
        r_f_c2544_profile._get_ixia_traffic_profile = mock.Mock()
        r_f_c2544_profile._ixia_traffic_generate = mock.Mock()
        r_f_c2544_profile.get_multiplier = mock.Mock()
        r_f_c2544_profile.tmp_throughput = 0
        r_f_c2544_profile.tmp_drop = 0
        r_f_c2544_profile.full_profile = {}
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "RxThroughput": 10,
                             "TxThroughput": 10,
                             "in_packets": 1000,
                             "out_packets": 1000}
        tol_min = 100.0
        tolerance = 0.0
        self.assertIsNotNone(r_f_c2544_profile.get_drop_percentage(
                             traffic_generator, samples,
                             tol_min, tolerance, ixia_obj))

    def test_get_drop_percentage_update(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        ixia_obj = mock.MagicMock()
        r_f_c2544_profile.execute = mock.Mock()
        r_f_c2544_profile._get_ixia_traffic_profile = mock.Mock()
        r_f_c2544_profile._ixia_traffic_generate = mock.Mock()
        r_f_c2544_profile.get_multiplier = mock.Mock()
        r_f_c2544_profile.tmp_throughput = 0
        r_f_c2544_profile.tmp_drop = 0
        r_f_c2544_profile.full_profile = {}
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "RxThroughput": 10,
                             "TxThroughput": 10,
                             "in_packets": 1000,
                             "out_packets": 1002}
        tol_min = 0.0
        tolerance = 1.0
        self.assertIsNotNone(r_f_c2544_profile.get_drop_percentage(
                             traffic_generator, samples,
                             tol_min, tolerance, ixia_obj))

    def test_get_drop_percentage_div_zero(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        ixia_obj = mock.MagicMock()
        r_f_c2544_profile.execute = mock.Mock()
        r_f_c2544_profile._get_ixia_traffic_profile = mock.Mock()
        r_f_c2544_profile._ixia_traffic_generate = mock.Mock()
        r_f_c2544_profile.get_multiplier = mock.Mock()
        r_f_c2544_profile.tmp_throughput = 0
        r_f_c2544_profile.tmp_drop = 0
        r_f_c2544_profile.full_profile = {}
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "RxThroughput": 10,
                             "TxThroughput": 10,
                             "in_packets": 1000,
                             "out_packets": 0}
        tol_min = 0.0
        tolerance = 0.0
        r_f_c2544_profile.tmp_throughput = 0
        self.assertIsNotNone(r_f_c2544_profile.get_drop_percentage(
                             traffic_generator, samples,
                             tol_min, tolerance, ixia_obj))

    def test_get_multiplier(self):
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.max_rate = 100
        r_f_c2544_profile.min_rate = 100
        self.assertEqual("1.0", r_f_c2544_profile.get_multiplier())

    def test_start_ixia_latency(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.max_rate = 100
        r_f_c2544_profile.min_rate = 100
        ixia_obj = mock.MagicMock()
        r_f_c2544_profile._get_ixia_traffic_profile = \
            mock.Mock(return_value={})
        r_f_c2544_profile.full_profile = {}
        r_f_c2544_profile._ixia_traffic_generate = mock.Mock()
        self.assertEqual(
            None,
            r_f_c2544_profile.start_ixia_latency(traffic_generator,
                                                 ixia_obj))


if __name__ == '__main__':
    unittest.main()
