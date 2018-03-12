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

# Unittest for yardstick.network_services.libs.ixia_libs.IxNet

from __future__ import absolute_import
import unittest
import mock

from yardstick.network_services.libs.ixia_libs.IxNet.IxNet import IxNextgen
from yardstick.network_services.libs.ixia_libs.IxNet.IxNet import IP_VERSION_4
from yardstick.network_services.libs.ixia_libs.IxNet.IxNet import IP_VERSION_6


UPLINK = "uplink"
DOWNLINK = "downlink"

class TestIxNextgen(unittest.TestCase):

    def test___init__(self):
        ixnet_gen = IxNextgen()
        self.assertIsNone(ixnet_gen._bidir)

    @mock.patch("yardstick.network_services.libs.ixia_libs.IxNet.IxNet.sys")
    def test_connect(self, *args):

        ixnet_gen = IxNextgen()
        ixnet_gen.get_config = mock.MagicMock()
        ixnet_gen.get_ixnet = mock.MagicMock()

        self.assertRaises(ImportError, ixnet_gen._connect, {"py_lib_path": "/tmp"})

    def test_clear_ixia_config(self):
        ixnet = mock.MagicMock()
        ixnet.execute = mock.Mock()

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.clear_ixia_config()
        self.assertIsNone(result)
        ixnet.execute.assert_called_once()

    def test_load_ixia_profile(self):
        ixnet = mock.MagicMock()
        ixnet.execute = mock.Mock()

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.load_ixia_profile({})
        self.assertIsNone(result)
        ixnet.execute.assert_called_once()

    def test_load_ixia_config(self):
        ixnet = mock.MagicMock()
        ixnet.execute = mock.Mock()

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_load_config({})
        self.assertIsNone(result)
        self.assertEqual(ixnet.execute.call_count, 2)

    @mock.patch('yardstick.network_services.libs.ixia_libs.IxNet.IxNet.log')
    def test_ix_assign_ports(self, mock_logger):
        ixnet = mock.MagicMock()
        ixnet.getList.return_value = [0, 1]
        ixnet.getAttribute.side_effect = ['up', 'down']

        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['2', '2'],
        }

        ixnet_gen = IxNextgen(ixnet)
        ixnet_gen._cfg = config

        result = ixnet_gen.ix_assign_ports()
        self.assertIsNone(result)
        ixnet.execute.assert_called_once()
        ixnet.commit.assert_called_once()
        self.assertEqual(ixnet.getAttribute.call_count, 2)
        mock_logger.error.assert_called_once()

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

        ixnet = mock.MagicMock()
        ixnet.remapIds.return_value = ["0"]
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]
        ixnet.getList.side_effect = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_update_frame(static_traffic_params)
        self.assertIsNone(result)
        self.assertEqual(ixnet.setMultiAttribute.call_count, 7)
        self.assertEqual(ixnet.commit.call_count, 2)

    def test_ix_update_udp(self):
        ixnet = mock.MagicMock()

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_update_udp({})
        self.assertIsNone(result)

    def test_ix_update_tcp(self):
        ixnet = mock.MagicMock()
        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_update_tcp({})
        self.assertIsNone(result)

    def test_ix_start_traffic(self):
        ixnet = mock.MagicMock()
        ixnet.getList.return_value = [0]
        ixnet.getAttribute.return_value = 'down'

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_start_traffic()
        self.assertIsNone(result)
        ixnet.getList.assert_called_once()
        self.assertEqual(ixnet.execute.call_count, 3)

    def test_ix_stop_traffic(self):
        ixnet = mock.MagicMock()
        ixnet.getList.return_value = [0]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_stop_traffic()
        self.assertIsNone(result)
        ixnet.getList.assert_called_once()
        ixnet.execute.assert_called_once()

    def test_ix_get_statistics(self):
        ixnet = mock.MagicMock()
        ixnet.execute.return_value = ""
        ixnet.getList.side_effect = [
            [
                '::ixNet::OBJ-/statistics/view:"Traffic Item Statistics"',
                '::ixNet::OBJ-/statistics/view:"Port Statistics"',
            ],
            [
                '::ixNet::OBJ-/statistics/view:"Flow Statistics"',
            ],
        ]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_get_statistics()
        self.assertIsNotNone(result)
        ixnet.getList.assert_called_once()
        self.assertEqual(ixnet.execute.call_count, 20)

    def test_find_view_obj_no_where(self):
        views = ['here', 'there', 'everywhere']
        result = IxNextgen.find_view_obj('no_where', views)
        self.assertEqual(result, '')

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

        ixnet = mock.MagicMock()
        ixnet.remapIds.return_value = ["0"]
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]
        ixnet.getList.side_effect = [[1], [0], [0], ["srcIp", "dstIp"]]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_params, IP_VERSION_4)
        self.assertIsNone(result)
        ixnet.setMultiAttribute.assert_called()
        ixnet.commit.assert_called_once()

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

        ixnet = mock.MagicMock()
        ixnet.remapIds.return_value = ["0"]
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]
        ixnet.getList.side_effect = [[1], [0, 1], [0], ["srcIp", "dstIp"]]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_params, IP_VERSION_4)
        self.assertIsNone(result)
        ixnet.setMultiAttribute.assert_called()
        ixnet.commit.assert_called_once()

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

        ixnet = mock.MagicMock()
        ixnet.getList.side_effect = [[1], [1], [1], ["srcIp", "dstIp"]]
        ixnet.remapIds.return_value = ["0"]
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_profile, IP_VERSION_6)
        self.assertIsNone(result)
        ixnet.setMultiAttribute.assert_called()
        ixnet.commit.assert_called_once()

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

        ixnet = mock.MagicMock()
        ixnet.getList.side_effect = [[1], [0, 1], [1], ["srcIP", "dstIP"]]
        ixnet.remapIds.return_value = ["0"]
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.add_ip_header(static_traffic_params, IP_VERSION_6)
        self.assertIsNone(result)
        ixnet.setMultiAttribute.assert_not_called()

    def test_set_random_ip_multi_attributes_bad_ip_version(self):
        bad_ip_version = object()
        ixnet_gen = IxNextgen(mock.Mock())
        mock1 = mock.Mock()
        mock2 = mock.Mock()
        mock3 = mock.Mock()
        with self.assertRaises(ValueError):
            ixnet_gen.set_random_ip_multi_attributes(mock1, bad_ip_version, mock2, mock3)

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
                    "py_lib_path": "test6",
                },
            }
        }

        expected = {
            'py_lib_path': 'test6',
            'machine': 'test1',
            'port': 'test5',
            'chassis': 'test4',
            'cards': ['0000', '0001'],
            'ports': ['07', '08'],
            'output_dir': 'test2',
            'version': 'test3',
            'bidir': True,
        }

        result = IxNextgen.get_config(tg_cfg)
        self.assertDictEqual(result, expected)

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

        ixnet = mock.MagicMock()
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]
        ixnet.getList.side_effect = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_update_ether(static_traffic_params)
        self.assertIsNone(result)
        ixnet.setMultiAttribute.assert_called()

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

        ixnet = mock.MagicMock()
        ixnet.setMultiAttribute.return_value = [1]
        ixnet.commit.return_value = [1]
        ixnet.getList.side_effect = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        ixnet_gen = IxNextgen(ixnet)

        result = ixnet_gen.ix_update_ether(static_traffic_params)
        self.assertIsNone(result)
        ixnet.setMultiAttribute.assert_not_called()
