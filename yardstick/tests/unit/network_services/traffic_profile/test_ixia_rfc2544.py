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

import copy

import mock
import unittest

from yardstick.network_services.traffic_profile import ixia_rfc2544
from yardstick.network_services.traffic_profile import trex_traffic_profile


class TestIXIARFC2544Profile(unittest.TestCase):

    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64,
        },
    }

    PROFILE = {
        'description': 'Traffic profile to run RFC2544 latency',
        'name': 'rfc2544',
        'traffic_profile': {
            'traffic_type': 'IXIARFC2544Profile',
            'frame_rate': 100},
        ixia_rfc2544.IXIARFC2544Profile.DOWNLINK: {
            'ipv4': {
                'outer_l2': {
                    'framesize': {
                        '64B': '100',
                        '1518B': '0',
                        '128B': '0',
                        '1400B': '0',
                        '256B': '0',
                        '373b': '0',
                        '570B': '0'}},
                'outer_l3v4': {
                    'dstip4': '1.1.1.1-1.15.255.255',
                    'proto': 'udp',
                    'count': '1',
                    'srcip4': '90.90.1.1-90.105.255.255',
                    'dscp': 0,
                    'ttl': 32},
                'outer_l4': {
                    'srcport': '2001',
                    'dsrport': '1234'}}},
        ixia_rfc2544.IXIARFC2544Profile.UPLINK: {
            'ipv4': {
                'outer_l2': {
                    'framesize': {
                        '64B': '100',
                        '1518B': '0',
                        '128B': '0',
                        '1400B': '0',
                        '256B': '0',
                        '373b': '0',
                        '570B': '0'}},
                'outer_l3v4': {
                    'dstip4': '9.9.1.1-90.105.255.255',
                    'proto': 'udp',
                    'count': '1',
                    'srcip4': '1.1.1.1-1.15.255.255',
                    'dscp': 0,
                    'ttl': 32},
                'outer_l4': {
                    'dstport': '2001',
                    'srcport': '1234'}}},
        'schema': 'isb:traffic_profile:0.1'}

    def test_get_ixia_traffic_profile_error(self):
        traffic_generator = mock.Mock(
            autospec=trex_traffic_profile.TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.uplink_ports = [-1]
        traffic_generator.downlink_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        STATIC_TRAFFIC = {
            ixia_rfc2544.IXIARFC2544Profile.UPLINK: {
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
            ixia_rfc2544.IXIARFC2544Profile.DOWNLINK: {
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

        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        mac = {"src_mac_0": "00:00:00:00:00:01",
               "src_mac_1": "00:00:00:00:00:02",
               "src_mac_2": "00:00:00:00:00:02",
               "dst_mac_0": "00:00:00:00:00:03",
               "dst_mac_1": "00:00:00:00:00:04",
               "dst_mac_2": "00:00:00:00:00:04"}
        result = r_f_c2544_profile._get_ixia_traffic_profile(self.PROFILE, mac)
        self.assertIsNotNone(result)

    def test_get_ixia_traffic_profile(self):
        traffic_generator = mock.Mock(
            autospec=trex_traffic_profile.TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.uplink_ports = [-1]
        traffic_generator.downlink_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        STATIC_TRAFFIC = {
            ixia_rfc2544.IXIARFC2544Profile.UPLINK: {
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
                    "ttl": 32,
                    "count": "1"
                },
                "outer_l3v6": {
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32,
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234",
                    "count": "1"
                },
                "traffic_type": "continuous"
            },
            ixia_rfc2544.IXIARFC2544Profile.DOWNLINK: {
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
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32,
                },
                "outer_l3v6": {
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32,
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001",
                    "count": "1"
                },
                "traffic_type": "continuous"
            }
        }
        ixia_rfc2544.STATIC_TRAFFIC = STATIC_TRAFFIC

        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        mac = {"src_mac_0": "00:00:00:00:00:01",
               "src_mac_1": "00:00:00:00:00:02",
               "src_mac_2": "00:00:00:00:00:02",
               "dst_mac_0": "00:00:00:00:00:03",
               "dst_mac_1": "00:00:00:00:00:04",
               "dst_mac_2": "00:00:00:00:00:04"}
        result = r_f_c2544_profile._get_ixia_traffic_profile(self.PROFILE, mac)
        self.assertIsNotNone(result)

    @mock.patch("yardstick.network_services.traffic_profile.ixia_rfc2544.open")
    def test_get_ixia_traffic_profile_v6(self, *args):
        traffic_generator = mock.Mock(
            autospec=trex_traffic_profile.TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.uplink_ports = [-1]
        traffic_generator.downlink_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        STATIC_TRAFFIC = {
            ixia_rfc2544.IXIARFC2544Profile.UPLINK: {
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
            ixia_rfc2544.IXIARFC2544Profile.DOWNLINK: {
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

        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
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
                        ixia_rfc2544.IXIARFC2544Profile.DOWNLINK:
                        {'ipv4':
                         {'outer_l2': {'framesize':
                                       {'64B': '100', '1518B': '0',
                                        '128B': '0', '1400B': '0',
                                        '256B': '0', '373b': '0',
                                        '570B': '0'}},
                          'outer_l3v4': {'dstip4': '1.1.1.1-1.15.255.255',
                                         'proto': 'udp', 'count': '1',
                                         'srcip4': '90.90.1.1-90.105.255.255',
                                         'dscp': 0, 'ttl': 32},
                          'outer_l3v6': {'dstip6': '1.1.1.1-1.15.255.255',
                                         'proto': 'udp', 'count': '1',
                                         'srcip6': '90.90.1.1-90.105.255.255',
                                         'dscp': 0, 'ttl': 32},
                          'outer_l4': {'srcport': '2001',
                                       'dsrport': '1234'}}},
                        ixia_rfc2544.IXIARFC2544Profile.UPLINK: {'ipv4':
                                                    {'outer_l2': {'framesize':
                                                                  {'64B': '100', '1518B': '0',
                                                                   '128B': '0', '1400B': '0',
                                                                   '256B': '0', '373b': '0',
                                                                   '570B': '0'}},
                                                        'outer_l3v4':
                                                        {'dstip4': '9.9.1.1-90.105.255.255',
                                                         'proto': 'udp', 'count': '1',
                                                         'srcip4': '1.1.1.1-1.15.255.255',
                                                         'dscp': 0, 'ttl': 32},
                                                        'outer_l3v6':
                                                        {'dstip6': '9.9.1.1-90.105.255.255',
                                                         'proto': 'udp', 'count': '1',
                                                         'srcip6': '1.1.1.1-1.15.255.255',
                                                         'dscp': 0, 'ttl': 32},

                                                        'outer_l4': {'dstport': '2001',
                                                                     'srcport': '1234'}}},
                        'schema': 'isb:traffic_profile:0.1'}
        result = r_f_c2544_profile._get_ixia_traffic_profile(profile_data, mac)
        self.assertIsNotNone(result)

    def test__init__(self):
        t_profile_data = copy.deepcopy(self.TRAFFIC_PROFILE)
        t_profile_data['traffic_profile']['frame_rate'] = 12345678
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(t_profile_data)
        self.assertEqual(12345678, r_f_c2544_profile.rate)

    def test__get_ip_and_mask_range(self):
        ip_range = '1.2.0.2-1.2.255.254'
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        ip, mask = r_f_c2544_profile._get_ip_and_mask(ip_range)
        self.assertEqual('1.2.0.2', ip)
        self.assertEqual(16, mask)

    def test__get_ip_and_mask_single(self):
        ip_range = '192.168.1.10'
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        ip, mask = r_f_c2544_profile._get_ip_and_mask(ip_range)
        self.assertEqual('192.168.1.10', ip)
        self.assertIsNone(mask)

    def test__get_fixed_and_mask_range(self):
        fixed_mask = '8-48'
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        fixed, mask = r_f_c2544_profile._get_fixed_and_mask(fixed_mask)
        self.assertEqual(8, fixed)
        self.assertEqual(48, mask)

    def test__get_fixed_and_mask_single(self):
        fixed_mask = 1234
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        fixed, mask = r_f_c2544_profile._get_fixed_and_mask(fixed_mask)
        self.assertEqual(1234, fixed)
        self.assertEqual(0, mask)

    def test__get_ixia_traffic_profile_default_args(self):
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)

        expected = {}
        result = r_f_c2544_profile._get_ixia_traffic_profile({})
        self.assertDictEqual(result, expected)

    def test__ixia_traffic_generate(self):
        traffic_generator = mock.Mock(
            autospec=trex_traffic_profile.TrexProfile)
        traffic_generator.networks = {
            "uplink_0": ["xe0"],
            "downlink_0": ["xe1"],
        }
        traffic_generator.client = \
            mock.Mock(return_value=True)
        traffic = {ixia_rfc2544.IXIARFC2544Profile.DOWNLINK: {'iload': 10},
                   ixia_rfc2544.IXIARFC2544Profile.UPLINK: {'iload': 10}}
        ixia_obj = mock.MagicMock()
        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(
            self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        result = r_f_c2544_profile._ixia_traffic_generate(traffic, ixia_obj)
        self.assertIsNone(result)

    def test_execute_traffic_first_run(self):
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.first_run = True
        rfc2544_profile.rate = 50
        with mock.patch.object(rfc2544_profile, '_get_ixia_traffic_profile') \
                as mock_get_tp, \
                mock.patch.object(rfc2544_profile, '_ixia_traffic_generate') \
                as mock_tgenerate, \
                mock.patch.object(rfc2544_profile, 'update_traffic_profile') \
                as mock_update_tp:
            mock_get_tp.return_value = 'fake_tprofile'
            output = rfc2544_profile.execute_traffic(mock.ANY,
                                                     ixia_obj=mock.ANY)

        self.assertTrue(output)
        self.assertFalse(rfc2544_profile.first_run)
        self.assertEqual(50, rfc2544_profile.max_rate)
        self.assertEqual(0, rfc2544_profile.min_rate)
        mock_get_tp.assert_called_once()
        mock_tgenerate.assert_called_once()
        mock_update_tp.assert_called_once()

    def test_execute_traffic_not_first_run(self):
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.first_run = False
        rfc2544_profile.max_rate = 70
        rfc2544_profile.min_rate = 0
        with mock.patch.object(rfc2544_profile, '_get_ixia_traffic_profile') \
                as mock_get_tp, \
                mock.patch.object(rfc2544_profile, '_ixia_traffic_generate') \
                as mock_tgenerate:
            mock_get_tp.return_value = 'fake_tprofile'
            rfc2544_profile.full_profile = mock.ANY
            output = rfc2544_profile.execute_traffic(mock.ANY,
                                                     ixia_obj=mock.ANY)

        self.assertFalse(output)
        self.assertEqual(35.0, rfc2544_profile.rate)
        mock_get_tp.assert_called_once()
        mock_tgenerate.assert_called_once()

    def test_update_traffic_profile(self):
        traffic_generator = mock.Mock(
            autospec=trex_traffic_profile.TrexProfile)
        traffic_generator.networks = {
            "uplink_0": ["xe0"],  # private, one value for intfs
            "downlink_0": ["xe1", "xe2"],  # public, two values for intfs
            "downlink_1": ["xe3"],  # not in TRAFFIC PROFILE
            "tenant_0": ["xe4"],  # not public or private
        }

        ports_expected = [8, 3, 5]
        traffic_generator.vnfd_helper.port_num.side_effect = ports_expected
        traffic_generator.client.return_value = True

        traffic_profile = copy.deepcopy(self.TRAFFIC_PROFILE)
        traffic_profile.update({
            "uplink_0": ["xe0"],
            "downlink_0": ["xe1", "xe2"],
        })

        r_f_c2544_profile = ixia_rfc2544.IXIARFC2544Profile(traffic_profile)
        r_f_c2544_profile.full_profile = {}
        r_f_c2544_profile.get_streams = mock.Mock()

        self.assertIsNone(
            r_f_c2544_profile.update_traffic_profile(traffic_generator))
        self.assertEqual(r_f_c2544_profile.ports, ports_expected)

    def test_get_drop_percentage_completed(self):
        samples = {'iface_name_1':
                       {'in_packets': 1000, 'out_packets': 1000,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25},
                   'iface_name_2':
                       {'in_packets': 1005, 'out_packets': 1007,
                        'Store-Forward_Avg_latency_ns': 23,
                        'Store-Forward_Min_latency_ns': 13,
                        'Store-Forward_Max_latency_ns': 28}
                   }
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        completed, samples = rfc2544_profile.get_drop_percentage(samples, 0, 1, 4)
        self.assertTrue(completed)
        self.assertEqual(66.9, samples['TxThroughput'])
        self.assertEqual(66.833, samples['RxThroughput'])
        self.assertEqual(0.099651, samples['DropPercentage'])
        self.assertEqual(21.5, samples['latency_ns_avg'])
        self.assertEqual(14.0, samples['latency_ns_min'])
        self.assertEqual(26.5, samples['latency_ns_max'])

    def test_get_drop_percentage_over_drop_percentage(self):
        samples = {'iface_name_1':
                       {'in_packets': 1000, 'out_packets': 1000,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25},
                   'iface_name_2':
                       {'in_packets': 1005, 'out_packets': 1007,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25}
                   }
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.rate = 1000
        completed, samples = rfc2544_profile.get_drop_percentage(
            samples, 0, 0.05, 4)
        self.assertFalse(completed)
        self.assertEqual(66.9, samples['TxThroughput'])
        self.assertEqual(66.833, samples['RxThroughput'])
        self.assertEqual(0.099651, samples['DropPercentage'])
        self.assertEqual(rfc2544_profile.rate, rfc2544_profile.max_rate)

    def test_get_drop_percentage_under_drop_percentage(self):
        samples = {'iface_name_1':
                       {'in_packets': 1000, 'out_packets': 1000,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25},
                   'iface_name_2':
                       {'in_packets': 1005, 'out_packets': 1007,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25}
                   }
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.rate = 1000
        completed, samples = rfc2544_profile.get_drop_percentage(
            samples, 0.2, 1, 4)
        self.assertFalse(completed)
        self.assertEqual(66.9, samples['TxThroughput'])
        self.assertEqual(66.833, samples['RxThroughput'])
        self.assertEqual(0.099651, samples['DropPercentage'])
        self.assertEqual(rfc2544_profile.rate, rfc2544_profile.min_rate)

    @mock.patch.object(ixia_rfc2544.LOG, 'info')
    def test_get_drop_percentage_not_flow(self, *args):
        samples = {'iface_name_1':
                       {'in_packets': 1000, 'out_packets': 0,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25},
                   'iface_name_2':
                       {'in_packets': 1005, 'out_packets': 0,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25}
                   }
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        rfc2544_profile.rate = 1000
        completed, samples = rfc2544_profile.get_drop_percentage(
            samples, 0.2, 1, 4)
        self.assertFalse(completed)
        self.assertEqual(0.0, samples['TxThroughput'])
        self.assertEqual(66.833, samples['RxThroughput'])
        self.assertEqual(100, samples['DropPercentage'])
        self.assertEqual(rfc2544_profile.rate, rfc2544_profile.max_rate)

    def test_get_drop_percentage_first_run(self):
        samples = {'iface_name_1':
                       {'in_packets': 1000, 'out_packets': 1000,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25},
                   'iface_name_2':
                       {'in_packets': 1005, 'out_packets': 1007,
                        'Store-Forward_Avg_latency_ns': 20,
                        'Store-Forward_Min_latency_ns': 15,
                        'Store-Forward_Max_latency_ns': 25}
                   }
        rfc2544_profile = ixia_rfc2544.IXIARFC2544Profile(self.TRAFFIC_PROFILE)
        completed, samples = rfc2544_profile.get_drop_percentage(
            samples, 0, 1, 4, first_run=True)
        self.assertTrue(completed)
        self.assertEqual(66.9, samples['TxThroughput'])
        self.assertEqual(66.833, samples['RxThroughput'])
        self.assertEqual(0.099651, samples['DropPercentage'])
        self.assertEqual(33.45, rfc2544_profile.rate)
