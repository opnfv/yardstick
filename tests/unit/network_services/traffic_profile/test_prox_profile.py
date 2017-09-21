# Copyright (c) 2017 Intel Corporation
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
from contextlib import contextmanager

import copy
import mock

from tests.unit import STL_MOCKS

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.traffic_profile.prox_profile import ProxProfile, \
        ProxTestDataTuple
    from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import TotStatsTuple, \
        ProxResourceHelper


class TestProxProfile(unittest.TestCase):

    VNFD0 = {
        'short-name': 'ProxVnf',
        'vdu': [
            {
                'routing_table': [
                    {
                        'network': '152.16.100.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'if': 'xe0',
                    },
                    {
                        'network': '152.16.40.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'if': 'xe1',
                    },
                ],
                'description': 'PROX approximation using DPDK',
                'name': 'proxvnf-baremetal',
                'nd_route_tbl': [
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0',
                    },
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1',
                    },
                ],
                'id': 'proxvnf-baremetal',
                'external-interface': [
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.0',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'vld_id': 'uplink_0',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 0,
                            'bandwidth': '10 Gbps',
                            'driver': "i40e",
                            'dst_ip': '152.16.100.19',
                            'local_iface_name': 'xe0',
                            'local_mac': '00:00:00:00:00:02',
                            'ifname': 'xe0',
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0',
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:03',
                            'vpci': '0000:05:00.1',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'vld_id': 'downlink_0',
                            'driver': "i40e",
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 1,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_iface_name': 'xe1',
                            'local_mac': '00:00:00:00:00:01',
                            'ifname': 'xe1',
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1',
                    },
                ],
            },
        ],
        'description': 'PROX approximation using DPDK',
        'mgmt-interface': {
            'vdu-id': 'proxvnf-baremetal',
            'host': '1.2.1.1',
            'password': 'r00t',
            'user': 'root',
            'ip': '1.2.1.1',
        },
        'benchmark': {
            'kpi': [
                'packets_in',
                'packets_fwd',
                'packets_dropped',
            ],
        },
        'id': 'ProxApproxVnf',
        'name': 'ProxVnf',
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD0,
            ],
        },
    }

    def test_fill_samples(self):
        samples = {}
        traffic_generator = mock.MagicMock()
        traffic_generator.vpci_if_name_ascending = [
            ['id1', 'name1'],
            ['id2', 'name2'],
        ]

        traffic_generator.resource_helper.sut.port_stats.side_effect = [
            list(range(12)),
            list(range(10, 22)),
        ]

        expected = {
            'name1': {
                'in_packets': 6,
                'out_packets': 7,
            },
            'name2': {
                'in_packets': 16,
                'out_packets': 17,
            },
        }
        ProxProfile.fill_samples(samples, traffic_generator)
        self.assertDictEqual(samples, expected)

    def test_init(self):
        tp_config = {
            'traffic_profile': {},
        }

        profile = ProxProfile(tp_config)
        profile.init(234)
        self.assertEqual(profile.queue, 234)

    def test_execute_traffic(self):
        packet_sizes = [
            10,
            100,
            1000,
        ]
        tp_config = {
            'traffic_profile': {
                'packet_sizes': packet_sizes,
            },
        }

        traffic_generator = mock.MagicMock()
        profile = ProxProfile(tp_config)

        self.assertFalse(profile.done)
        for _ in packet_sizes:
            with self.assertRaises(NotImplementedError):
                profile.execute_traffic(traffic_generator)

        self.assertIsNone(profile.execute_traffic(traffic_generator))

    def test_bounds_iterator(self):
        tp_config = {
            'traffic_profile': {},
        }

        profile = ProxProfile(tp_config)
        value = 0.0
        for value in profile.bounds_iterator():
            pass

        self.assertEqual(value, 100.0)

        mock_logger = mock.MagicMock()
        for _ in profile.bounds_iterator(mock_logger):
            pass

        self.assertEqual(mock_logger.debug.call_count, 1)
        self.assertEqual(mock_logger.info.call_count, 10)

    @mock.patch('yardstick.network_services.traffic_profile.prox_profile.time')
    def test_run_test(self, mock_time):
        @contextmanager
        def measure(*args, **kwargs):
            yield stats

        bad_vnfd = copy.deepcopy(self.VNFD0)
        bad_vnfd['vdu'][0]['external-interface'].append({
            'virtual-interface': {
                'dst_mac': '00:00:00:00:00:05',
                'vpci': '0000:06:00.0',
                'local_ip': '152.16.100.20',
                'type': 'PCI-PASSTHROUGH',
                'vld_id': 'uplink_1',
                'netmask': '255.255.255.0',
                'dpdk_port_num': 0,
                'bandwidth': '10 Gbps',
                'driver': "i40e",
                'dst_ip': '152.16.100.20',
                'local_iface_name': 'xe2',
                'local_mac': '00:00:00:00:00:07',
                'ifname': 'xe2',
            },
            'vnfd-connection-point-ref': 'xe2',
            'name': 'xe2',
        })

        bad_vnfd_helper = VnfdHelper(bad_vnfd)
        setup_helper = mock.MagicMock()
        setup_helper.vnfd_helper = bad_vnfd_helper

        stats = {
            'delta': TotStatsTuple(6, 7, 8, 9),
        }

        client = mock.MagicMock()
        client.hz.return_value = 2
        client.measure_tot_stats = measure
        client.port_stats.return_value = tuple(range(12))

        tp_config = {
            'traffic_profile': {},
        }

        profile = ProxProfile(tp_config)

        helper = ProxResourceHelper(setup_helper)
        helper.client = client
        helper.get_latency = mock.MagicMock(return_value=[3.3, 3.6, 3.8])

        with self.assertRaises(AssertionError):
            profile.run_test(helper, 980, 15, 45)

        vnfd_helper = VnfdHelper(self.VNFD0)
        setup_helper.vnfd_helper = vnfd_helper
        helper = ProxResourceHelper(setup_helper)
        helper.client = client
        helper.get_latency = mock.MagicMock(return_value=[3.3, 3.6, 3.8])
        helper._test_cores = [3, 4]

        expected_test_data = ProxTestDataTuple(0.0, 2.0, 6, 7, 8, [3.3, 3.6, 3.8], 6, 7, 6.5e6)
        expected_port_samples = {
            'xe0': {'in_packets': 6, 'out_packets': 7},
            'xe1': {'in_packets': 6, 'out_packets': 7},
        }
        test_data, port_samples = profile.run_test(helper, 230, 60, 65)
        self.assertTupleEqual(test_data, expected_test_data)
        self.assertDictEqual(port_samples, expected_port_samples)


class TestProxTestDataTuple(unittest.TestCase):
    def test___init__(self):
        prox_test_data = ProxTestDataTuple(1, 2, 3, 4, 5, 6, 7, 8, 9)
        self.assertEqual(prox_test_data.tolerated, 1)
        self.assertEqual(prox_test_data.tsc_hz, 2)
        self.assertEqual(prox_test_data.delta_rx, 3)
        self.assertEqual(prox_test_data.delta_tx, 4)
        self.assertEqual(prox_test_data.delta_tsc, 5)
        self.assertEqual(prox_test_data.latency, 6)
        self.assertEqual(prox_test_data.rx_total, 7)
        self.assertEqual(prox_test_data.tx_total, 8)
        self.assertEqual(prox_test_data.pps, 9)

    def test_properties(self):
        prox_test_data = ProxTestDataTuple(1, 2, 3, 4, 5, 6, 7, 8, 9)
        self.assertEqual(prox_test_data.pkt_loss, 12.5)
        self.assertEqual(prox_test_data.mpps, 1.6 / 1e6)
        self.assertEqual(prox_test_data.can_be_lost, 0)
        self.assertEqual(prox_test_data.drop_total, 1)
        self.assertFalse(prox_test_data.success)

        prox_test_data = ProxTestDataTuple(10, 2, 3, 4, 5, 6, 997, 998, 9)
        self.assertTrue(prox_test_data.success)

    def test_pkt_loss_zero_division(self):
        prox_test_data = ProxTestDataTuple(1, 2, 3, 4, 5, 6, 7, 0, 9)
        self.assertEqual(prox_test_data.pkt_loss, 100.0)

    def test_get_samples(self):
        prox_test_data = ProxTestDataTuple(1, 2, 3, 4, 5, [6.1, 6.9, 6.4], 7, 8, 9)

        expected = {
            "Throughput": 1.6 / 1e6,
            "DropPackets": 12.5,
            "CurrentDropPackets": 12.5,
            "TxThroughput": 9 / 1e6,
            "RxThroughput": 1.6 / 1e6,
            "PktSize": 64,
            "PortSample": 1,
            "LatencyMin": 6.1,
            "LatencyMax": 6.9,
            "LatencyAvg": 6.4,
        }
        result = prox_test_data.get_samples(64, port_samples={"PortSample": 1})
        self.assertDictEqual(result, expected)

        expected = {
            "Throughput": 1.6 / 1e6,
            "DropPackets": 0.123,
            "CurrentDropPackets": 0.123,
            "TxThroughput": 9 / 1e6,
            "RxThroughput": 1.6 / 1e6,
            "PktSize": 64,
            "LatencyMin": 6.1,
            "LatencyMax": 6.9,
            "LatencyAvg": 6.4,
        }
        result = prox_test_data.get_samples(64, 0.123)
        self.assertDictEqual(result, expected)

    @mock.patch('yardstick.network_services.traffic_profile.prox_profile.LOG')
    def test_log_data(self, mock_logger):
        my_mock_logger = mock.MagicMock()
        prox_test_data = ProxTestDataTuple(1, 2, 3, 4, 5, [6.1, 6.9, 6.4], 7, 8, 9)
        prox_test_data.log_data()
        self.assertEqual(my_mock_logger.debug.call_count, 0)
        self.assertEqual(mock_logger.debug.call_count, 2)

        mock_logger.debug.reset_mock()
        prox_test_data.log_data(my_mock_logger)
        self.assertEqual(my_mock_logger.debug.call_count, 2)
        self.assertEqual(mock_logger.debug.call_count, 0)
