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

import unittest
import mock

from tests.unit import STL_MOCKS


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.traffic_profile.trex_traffic_profile \
        import TrexProfile
    from yardstick.network_services.traffic_profile.rfc2544 import \
        RFC2544Profile


class TestRFC2544Profile(unittest.TestCase):
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
               'downlink_0': {'ipv4':
                              {'outer_l2': {'framesize':
                                            {'64B': '100', '1518B': '0',
                                             '128B': '0', '1400B': '0',
                                             '256B': '0', '373b': '0',
                                             '570B': '0'}},
                               'outer_l3v4': {'dstip4': '1.1.1.1-1.15.255.255',
                                              'proto': 'udp',
                                              'srcip4': '90.90.1.1-90.105.255.255',
                                              'dscp': 0, 'ttl': 32, 'count': 1},
                               'outer_l4': {'srcport': '2001',
                                            'dsrport': '1234', 'count': 1}}},
               'uplink_0': {'ipv4':
                            {'outer_l2': {'framesize':
                                          {'64B': '100', '1518B': '0',
                                           '128B': '0', '1400B': '0',
                                           '256B': '0', '373b': '0',
                                           '570B': '0'}},
                             'outer_l3v4': {'dstip4': '9.9.1.1-90.105.255.255',
                                            'proto': 'udp',
                                            'srcip4': '1.1.1.1-1.15.255.255',
                                            'dscp': 0, 'ttl': 32, 'count': 1},
                             'outer_l4': {'dstport': '2001',
                                          'srcport': '1234', 'count': 1}}},
               'schema': 'isb:traffic_profile:0.1'}

    def test___init__(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        self.assertIsNotNone(r_f_c2544_profile.rate)

    def test_execute(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.networks = {
            "uplink_0": ["xe0"],
            "downlink_0": ["xe1"],
        }
        traffic_generator.client.return_value = True
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        r_f_c2544_profile.first_run = True
        self.assertIsNone(r_f_c2544_profile.execute_traffic(traffic_generator))

    def test_get_drop_percentage(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.networks = {
            "uplink_0": ["xe0"],
            "downlink_0": ["xe1"],
        }
        traffic_generator.client.return_value = True

        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        r_f_c2544_profile.register_generator(traffic_generator)
        self.assertIsNone(r_f_c2544_profile.execute_traffic(traffic_generator))

        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {
                "rx_throughput_fps": 20,
                "tx_throughput_fps": 20,
                "rx_throughput_mbps": 10,
                "tx_throughput_mbps": 10,
                "in_packets": 1000,
                "out_packets": 1000,
            }

        expected = {
            'DropPercentage': 0.0,
            'RxThroughput': 100 / 3.0,
            'TxThroughput': 100 / 3.0,
            'CurrentDropPercentage': 0.0,
            'Throughput': 66.66666666666667,
            'xe0': {
                'tx_throughput_fps': 20,
                'in_packets': 1000,
                'out_packets': 1000,
                'rx_throughput_mbps': 10,
                'tx_throughput_mbps': 10,
                'rx_throughput_fps': 20,
            },
        }
        traffic_generator.generate_samples.return_value = samples
        traffic_generator.RUN_DURATION = 30
        traffic_generator.rfc2544_helper.tolerance_low = 0.0001
        traffic_generator.rfc2544_helper.tolerance_high = 0.0001
        result = r_f_c2544_profile.get_drop_percentage(traffic_generator)
        self.assertDictEqual(result, expected)

    def test_get_drop_percentage_update(self):
        traffic_generator = mock.Mock(autospec=RFC2544Profile)
        traffic_generator.networks = {
            "uplink_0": ["xe0"],
            "downlink_0": ["xe1"],
        }
        traffic_generator.client = mock.Mock(return_value=True)

        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        r_f_c2544_profile.register_generator(traffic_generator)
        self.assertIsNone(r_f_c2544_profile.execute_traffic())

        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {
                "rx_throughput_fps": 20,
                "tx_throughput_fps": 20,
                "rx_throughput_mbps": 10,
                "tx_throughput_mbps": 10,
                "in_packets": 1000,
                "out_packets": 1002,
            }
        expected = {
            'DropPercentage': 0.1996,
            'RxThroughput': 33.333333333333336,
            'TxThroughput': 33.4,
            'CurrentDropPercentage': 0.1996,
            'Throughput': 66.66666666666667,
            'xe0': {
                'tx_throughput_fps': 20,
                'in_packets': 1000,
                'out_packets': 1002,
                'rx_throughput_mbps': 10,
                'tx_throughput_mbps': 10,
                'rx_throughput_fps': 20,
            },
        }
        traffic_generator.generate_samples = mock.MagicMock(
            return_value=samples)
        traffic_generator.RUN_DURATION = 30
        traffic_generator.rfc2544_helper.tolerance_low = 0.0001
        traffic_generator.rfc2544_helper.tolerance_high = 0.0001
        result = r_f_c2544_profile.get_drop_percentage(traffic_generator)
        self.assertDictEqual(expected, result)

    def test_get_drop_percentage_div_zero(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.networks = {
            "uplink_0": ["xe0"],
            "downlink_0": ["xe1"],
        }
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        self.assertIsNone(r_f_c2544_profile.execute_traffic(traffic_generator))
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "in_packets": 1000,
                             "out_packets": 0}
        r_f_c2544_profile.throughput_max = 0
        expected = {
            'DropPercentage': 100.0, 'RxThroughput': 100 / 3.0,
            'TxThroughput': 0.0, 'CurrentDropPercentage': 100.0,
            'Throughput': 66.66666666666667,
            'xe0': {
                'tx_throughput_fps': 20, 'in_packets': 1000,
                'out_packets': 0, 'rx_throughput_mbps': 10,
                'tx_throughput_mbps': 10, 'rx_throughput_fps': 20
            }
        }
        traffic_generator.generate_samples = mock.Mock(return_value=samples)
        traffic_generator.RUN_DURATION = 30
        traffic_generator.rfc2544_helper.tolerance_low = 0.0001
        traffic_generator.rfc2544_helper.tolerance_high = 0.0001
        self.assertDictEqual(expected,
                             r_f_c2544_profile.get_drop_percentage(traffic_generator))

    def test_get_multiplier(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.max_rate = 100
        r_f_c2544_profile.min_rate = 100
        self.assertEqual("1.0", r_f_c2544_profile.get_multiplier())

    def test_calculate_pps(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.rate = 100
        r_f_c2544_profile.pps = 100
        samples = {'Throughput': 4549093.33}
        self.assertEqual((2274546.67, 1.0),
                         r_f_c2544_profile.calculate_pps(samples))

    def test_create_single_stream(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile._create_single_packet = mock.MagicMock()
        r_f_c2544_profile.pg_id = 1
        self.assertIsNotNone(
            r_f_c2544_profile.create_single_stream(64, 2274546.67))

    def test_create_single_stream_no_pg_id(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile._create_single_packet = mock.MagicMock()
        r_f_c2544_profile.pg_id = 0
        self.assertIsNotNone(
            r_f_c2544_profile.create_single_stream(64, 2274546.67))

    def test_execute_latency(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.networks = {
            "private_0": ["xe0"],
            "public_0": ["xe1"],
        }
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        r_f_c2544_profile.first_run = True
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "in_packets": 1000,
                             "out_packets": 0}

        samples['Throughput'] = 4549093.33
        r_f_c2544_profile.calculate_pps = mock.Mock(return_value=[2274546.67,
                                                                  1.0])

        self.assertIsNone(r_f_c2544_profile.execute_latency(traffic_generator,
                                                            samples))
