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

    def test___init__(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        assert r_f_c2544_profile.rate

    def test_execute(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [-1]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        r_f_c2544_profile.first_run = True
        self.assertEqual(None, r_f_c2544_profile.execute(traffic_generator))

    def test_get_drop_percentage(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        self.assertEqual(None, r_f_c2544_profile.execute(traffic_generator))
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "in_packets": 1000,
                             "out_packets": 1000}
        tol_min = 100.0
        tolerance = 0.0
        expected = {'DropPercentage': 0.0, 'RxThroughput': 100/3.0,
                    'TxThroughput': 100/3.0, 'CurrentDropPercentage': 0.0,
                    'Throughput': 100/3.0,
                    'xe0': {'tx_throughput_fps': 20, 'in_packets': 1000,
                            'out_packets': 1000, 'rx_throughput_mbps': 10,
                            'tx_throughput_mbps': 10, 'rx_throughput_fps': 20}}
        self.assertDictEqual(expected,
                             r_f_c2544_profile.get_drop_percentage(
                                 traffic_generator, samples,
                                 tol_min, tolerance))

    def test_get_drop_percentage_update(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        self.assertEqual(None, r_f_c2544_profile.execute(traffic_generator))
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "in_packets": 1000,
                             "out_packets": 1002}
        tol_min = 0.0
        tolerance = 1.0
        expected = {'DropPercentage': 0.2, 'RxThroughput': 100/3.0,
                    'TxThroughput': 33.4, 'CurrentDropPercentage': 0.2,
                    'Throughput': 100/3.0,
                    'xe0': {'tx_throughput_fps': 20, 'in_packets': 1000,
                            'out_packets': 1002, 'rx_throughput_mbps': 10,
                            'tx_throughput_mbps': 10, 'rx_throughput_fps': 20}}
        self.assertDictEqual(expected,
                             r_f_c2544_profile.get_drop_percentage(
                                 traffic_generator, samples,
                                 tol_min, tolerance))

    def test_get_drop_percentage_div_zero(self):
        traffic_generator = mock.Mock(autospec=TrexProfile)
        traffic_generator.my_ports = [0, 1]
        traffic_generator.priv_ports = [0]
        traffic_generator.pub_ports = [1]
        traffic_generator.client = \
            mock.Mock(return_value=True)
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.params = self.PROFILE
        self.assertEqual(None, r_f_c2544_profile.execute(traffic_generator))
        samples = {}
        for ifname in range(1):
            name = "xe{}".format(ifname)
            samples[name] = {"rx_throughput_fps": 20,
                             "tx_throughput_fps": 20,
                             "rx_throughput_mbps": 10,
                             "tx_throughput_mbps": 10,
                             "in_packets": 1000,
                             "out_packets": 0}
        tol_min = 0.0
        tolerance = 0.0
        r_f_c2544_profile.tmp_throughput = 0
        expected = {'DropPercentage': 100.0, 'RxThroughput': 100/3.0,
                    'TxThroughput': 0.0, 'CurrentDropPercentage': 100.0,
                    'Throughput': 100/3.0,
                    'xe0': {'tx_throughput_fps': 20, 'in_packets': 1000,
                            'out_packets': 0, 'rx_throughput_mbps': 10,
                            'tx_throughput_mbps': 10, 'rx_throughput_fps': 20}}
        self.assertDictEqual(expected,
                             r_f_c2544_profile.get_drop_percentage(
                                 traffic_generator, samples,
                                 tol_min, tolerance))

    def test_get_multiplier(self):
        r_f_c2544_profile = RFC2544Profile(self.TRAFFIC_PROFILE)
        r_f_c2544_profile.max_rate = 100
        r_f_c2544_profile.min_rate = 100
        self.assertEqual("1.0", r_f_c2544_profile.get_multiplier())

if __name__ == '__main__':
    unittest.main()
