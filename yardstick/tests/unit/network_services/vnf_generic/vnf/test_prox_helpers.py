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

from itertools import repeat, chain
import os
import socket
import time

import mock
import unittest

from tests.unit import STL_MOCKS
from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services import constants

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxSocketHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import PacketDump
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import CoreSocketTuple
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxTestDataTuple
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxDpdkVnfSetupEnvHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import TotStatsTuple
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxDataHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxResourceHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxProfileHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxMplsProfileHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxBngProfileHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxVpeProfileHelper
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxlwAFTRProfileHelper

class TestCoreTuple(unittest.TestCase):
    def test___init__(self):
        core_tuple = CoreSocketTuple('core 5s6')
        self.assertEqual(core_tuple.core_id, 5)
        self.assertEqual(core_tuple.socket_id, 6)
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = CoreSocketTuple('core 5s6h')
        self.assertEqual(core_tuple.core_id, 5)
        self.assertEqual(core_tuple.socket_id, 6)
        self.assertTrue(core_tuple.is_hyperthread())

    def test___init__negative(self):
        bad_inputs = [
            '',
            '5',
            '5s',
            '6h',
            '5s6',
            'core',
            'core h',
            'core 5s',
            'core 5 6',
            'core 5 6h',
            'core 5d6',
            'core 5d6h',
            1,
            2.3,
            [],
            {},
            object(),
        ]

        for bad_input in bad_inputs:
            with self.assertRaises(ValueError):
                CoreSocketTuple(bad_input)

    def test_find_in_topology(self):
        topology_in = {
            6: {
                5: {
                    'key1': ['a', 'b'],
                    'key2': ['c', 'd'],
                },
            },
        }

        core_tuple = CoreSocketTuple('core 5s6')

        expected = 'a'
        result = core_tuple.find_in_topology(topology_in)
        self.assertEqual(result, expected)

        core_tuple = CoreSocketTuple('core 5s6h')

        expected = 'c'
        result = core_tuple.find_in_topology(topology_in)
        self.assertEqual(result, expected)

    def test_find_in_topology_negative(self):
        core_tuple = CoreSocketTuple('core 6s5')
        with self.assertRaises(ValueError):
            # no socket key
            core_tuple.find_in_topology({})

        with self.assertRaises(ValueError):
            # no core key
            core_tuple.find_in_topology({5: {}})

        with self.assertRaises(ValueError):
            # no first value (as needed by non-hyperthread core)
            core_tuple.find_in_topology({5: {6: {'key1': []}}})

        core_tuple = CoreSocketTuple('core 6s5h')
        with self.assertRaises(ValueError):
            # no second value (as needed by hyperthread core)
            core_tuple.find_in_topology({5: {6: {'key1': ['e']}}})


class TestTotStatsTuple(unittest.TestCase):
    def test___new___negative(self):
        with self.assertRaises(TypeError):
            # no values
            TotStatsTuple()

        with self.assertRaises(TypeError):
            # one, non-integer value
            TotStatsTuple('a')

        with self.assertRaises(TypeError):
            # too many values
            TotStatsTuple(3, 4, 5, 6, 7)


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

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.LOG')
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


class TestPacketDump(unittest.TestCase):
    PAYLOAD = "payload"

    def test__init__(self):
        PacketDump("port_id", len(self.PAYLOAD), self.PAYLOAD)

    def test___str__(self):
        expected = '<PacketDump port: port_id payload: {}>'.format(self.PAYLOAD)
        dump1 = PacketDump("port_id", len(self.PAYLOAD), self.PAYLOAD)
        self.assertEqual(str(dump1), expected)

    def test_port_id(self):
        p = PacketDump("port_id", len(self.PAYLOAD), self.PAYLOAD)
        self.assertEqual(p.port_id, "port_id")

    def test_data_len(self):
        p = PacketDump("port_id", len(self.PAYLOAD), self.PAYLOAD)
        self.assertEqual(p.data_len, len(self.PAYLOAD))

    def test_payload(self):
        p = PacketDump("port_id", len(self.PAYLOAD), self.PAYLOAD)
        self.assertEqual(p.payload(), self.PAYLOAD)

        self.assertEqual(p.payload(3), self.PAYLOAD[3:])

        self.assertEqual(p.payload(end=3), self.PAYLOAD[:4])

        self.assertEqual(p.payload(2, 4), self.PAYLOAD[2:5])


PACKET_DUMP_1 = """\
pktdump,3,11
hello world
"""

PACKET_DUMP_2 = """\
pktdump,3,11
hello world
pktdump,2,9
brown fox jumped over
pktdump,4,8
lazy
dog
"""

PACKET_DUMP_NON_1 = """\
not_a_dump,1,2
other data
"""

PACKET_DUMP_MIXED_1 = """\
pktdump,3,11
hello world
not_a_dump,1,2
other data
"""

PACKET_DUMP_BAD_1 = """\
pktdump,one,12
bad port id
"""

PACKET_DUMP_BAD_2 = """\
pktdump,3,twelve
bad data length
"""

PACKET_DUMP_BAD_3 = """\
pktdump,3
no data length value
"""


class TestProxSocketHelper(unittest.TestCase):

    def setUp(self):
        self.mock_time_sleep = mock.patch.object(time, 'sleep').start()

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    def test___init__(self, mock_socket):
        expected = mock_socket.socket()
        prox = ProxSocketHelper()
        result = prox._sock
        self.assertEqual(result, expected)

    def test_connect(self):
        mock_sock = mock.MagicMock()
        prox = ProxSocketHelper(mock_sock)
        prox.connect('10.20.30.40', 23456)
        self.assertEqual(mock_sock.connect.call_count, 1)

    def test_get_sock(self):
        mock_sock = mock.MagicMock()
        prox = ProxSocketHelper(mock_sock)
        result = prox.get_socket()
        self.assertIs(result, mock_sock)

    # TODO(elfoley): Split this into three tests
    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.select')
    def test_get_data(self, mock_select):
        mock_select.select.side_effect = [[1], [0]]
        mock_socket = mock.MagicMock()
        mock_recv = mock_socket.recv()
        mock_recv.decode.return_value = ""
        prox = ProxSocketHelper(mock_socket)
        ret = prox.get_data()
        self.assertEqual(ret, "")
        self.assertEqual(len(prox._pkt_dumps), 0)

        mock_select.select.reset_mock()
        mock_select.select.side_effect = chain([['a'], ['']], repeat([1], 3))
        mock_recv.decode.return_value = PACKET_DUMP_1
        ret = prox.get_data()
        self.assertEqual(mock_select.select.call_count, 2)
        self.assertEqual(ret, 'pktdump,3,11')
        self.assertEqual(len(prox._pkt_dumps), 1)

        mock_select.select.reset_mock()
        mock_select.select.side_effect = chain([[object()], [None]], repeat([1], 3))
        mock_recv.decode.return_value = PACKET_DUMP_2
        ret = prox.get_data()
        self.assertEqual(mock_select.select.call_count, 2)
        self.assertEqual(ret, 'jumped over')
        self.assertEqual(len(prox._pkt_dumps), 3)

    def test__parse_socket_data_mixed_data(self):
        prox = ProxSocketHelper(mock.MagicMock())
        ret = prox._parse_socket_data(PACKET_DUMP_NON_1, False)
        self.assertEqual(ret, 'not_a_dump,1,2')
        self.assertEqual(len(prox._pkt_dumps), 0)

        ret = prox._parse_socket_data(PACKET_DUMP_MIXED_1, False)
        self.assertEqual(ret, 'not_a_dump,1,2')
        self.assertEqual(len(prox._pkt_dumps), 1)

    def test__parse_socket_data_bad_data(self):
        prox = ProxSocketHelper(mock.MagicMock())
        with self.assertRaises(ValueError):
            prox._parse_socket_data(PACKET_DUMP_BAD_1, False)

        with self.assertRaises(ValueError):
            prox._parse_socket_data(PACKET_DUMP_BAD_2, False)

        ret = prox._parse_socket_data(PACKET_DUMP_BAD_3, False)
        self.assertEqual(ret, 'pktdump,3')

    def test__parse_socket_data_pkt_dump_only(self):
        prox = ProxSocketHelper(mock.MagicMock())
        ret = prox._parse_socket_data('', True)
        self.assertFalse(ret)

        ret = prox._parse_socket_data(PACKET_DUMP_1, True)
        self.assertTrue(ret)

        ret = prox._parse_socket_data(PACKET_DUMP_2, True)
        self.assertTrue(ret)

    def test_put_command(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.put_command("data")
        mock_socket.sendall.assert_called_once()

    def test_put_command_socket_error(self):
        mock_socket = mock.MagicMock()
        mock_socket.sendall.side_effect = OSError
        prox = ProxSocketHelper(mock_socket)
        prox.put_command("data")
        mock_socket.sendall.assert_called_once()

    def test_get_packet_dump(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox._pkt_dumps = []
        self.assertIsNone(prox.get_packet_dump())

        prox._pkt_dumps = [234]
        self.assertEqual(prox.get_packet_dump(), 234)
        self.assertEqual(prox._pkt_dumps, [])

    def test_stop_all_reset(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.stop_all_reset()
        mock_socket.sendall.assert_called()

    def test_stop_all(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.stop_all()
        mock_socket.sendall.assert_called()

    def test_stop(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.stop([3, 4, 5], 16)
        mock_socket.sendall.assert_called()

    def test_start_all(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.start_all()
        mock_socket.sendall.assert_called()

    def test_start(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.start([3, 4, 5])
        mock_socket.sendall.assert_called()

    def test_reset_stats(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.reset_stats()
        mock_socket.sendall.assert_called()

    def test_set_pkt_size(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.set_pkt_size([3, 4, 5], 1024)
        self.assertEqual(mock_socket.sendall.call_count, 3)

    def test_set_value(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.set_value([3, 4, 5], 10, 20, 30)
        self.assertEqual(mock_socket.sendall.call_count, 3)

    def test_reset_values(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.reset_values([3, 4, 5])
        self.assertEqual(mock_socket.sendall.call_count, 3)

    def test_set_speed(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.set_speed([3, 4, 5], 1000)
        self.assertEqual(mock_socket.sendall.call_count, 3)

    def test_slope_speed(self):
        core_data = [
            {
                'cores': [3, 4, 5],
                'speed': 1000,
            },
            {
                'cores': [9, 10, 11],
                'speed': '500.5',
            },
        ]

        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.set_speed = set_speed = mock.MagicMock()
        prox.slope_speed(core_data, 5)
        self.assertEqual(set_speed.call_count, 20)

        set_speed.reset_mock()
        prox.slope_speed(core_data, 5, 5)
        self.assertEqual(set_speed.call_count, 10)

    def test_set_pps(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.set_pps([3, 4, 5], 1000, 512)
        self.assertEqual(mock_socket.sendall.call_count, 3)

    def test_lat_stats(self):
        latency_output = [
            '1, 2 , 3',  # has white space
            '4,5',  # too short
            '7,8,9,10.5,11',  # too long with float, but float is in unused portion
            'twelve,13,14',  # value as English word
            '15,16.2,17',  # float in used portion
        ]

        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(side_effect=latency_output)

        expected = (
            {
                3: 1,
                5: 7,
            },
            {
                3: 2,
                5: 8,
            },
            {
                3: 3,
                5: 9,
            },
        )
        result = prox.lat_stats([3, 4, 5, 6, 7], 16)
        self.assertEqual(mock_socket.sendall.call_count, 5)
        self.assertEqual(result, expected)

    def test_get_all_tot_stats_error(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(return_value='3,4,5')
        expected = [0, 0, 0, 0]
        result = prox.get_all_tot_stats()
        self.assertEqual(result, expected)

    def test_get_all_tot_stats(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(return_value='3,4,5,6')
        expected = 3, 4, 5, 6
        result = prox.get_all_tot_stats()
        self.assertEqual(result, expected)

    def test_hz(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(return_value='3,4,5,6')
        expected = 6
        result = prox.hz()
        self.assertEqual(result, expected)

    def test_core_stats(self):
        core_stats = [
            '3,4,5,6',
            '7,8,9,10,NaN',
            '11,12,13,14,15',
        ]

        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(side_effect=core_stats)
        expected = 21, 24, 27, 14
        result = prox.core_stats([3, 4, 5], 16)
        self.assertEqual(result, expected)

    def test_port_stats(self):
        port_stats = [
            ','.join(str(n) for n in range(3, 15)),
            ','.join(str(n) for n in range(8, 32, 2)),
            ','.join(str(n) for n in range(5, 89, 7)),
        ]

        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(side_effect=port_stats)
        expected = [16, 26, 36, 46, 56, 66, 76, 86, 96, 106, 116, 126]
        result = prox.port_stats([3, 4, 5])
        self.assertEqual(result, expected)

    def test_measure_tot_stats(self):
        start_tot = 3, 4, 5, 6
        end_tot = 7, 9, 11, 13
        delta_tot = 4, 5, 6, 7

        get_data_output = [
            ','.join(str(n) for n in start_tot),
            ','.join(str(n) for n in end_tot),
        ]

        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(side_effect=get_data_output)
        expected = {
            'start_tot': start_tot,
            'end_tot': end_tot,
            'delta': delta_tot,
        }
        with prox.measure_tot_stats() as result:
            pass
        self.assertEqual(result, expected)

    def test_tot_stats(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(return_value='3,4,5,6')
        expected = 3, 4, 5
        result = prox.tot_stats()
        self.assertEqual(result, expected)

    def test_tot_ierrors(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.get_data = mock.MagicMock(return_value='3,4,5,6')
        expected = 3, 3
        result = prox.tot_ierrors()
        self.assertEqual(result, expected)

    def test_set_count(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.set_count(432, [3, 4, 5])
        self.assertEqual(mock_socket.sendall.call_count, 3)

    def test_dump_rx(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.dump_rx(3, 5, 8)
        self.assertEqual(mock_socket.sendall.call_count, 1)

    def test_quit(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.quit()
        mock_socket.sendall.assert_called()

    def test_force_quit(self):
        mock_socket = mock.MagicMock()
        prox = ProxSocketHelper(mock_socket)
        prox.force_quit()
        mock_socket.sendall.assert_called()


class TestProxDpdkVnfSetupEnvHelper(unittest.TestCase):

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

    def test_global_section(self):
        setup_helper = ProxDpdkVnfSetupEnvHelper(mock.MagicMock(), mock.MagicMock(),
                                                 mock.MagicMock())

        setup_helper._prox_config_data = [('a', [])]

        with self.assertRaises(KeyError):
            _ = setup_helper.global_section

        global_section = (
            'global', [
                ('not_name', 'other data'),
                ('name_not', 'more data'),
                ('name', 'prox type'),
            ],
        )

        setup_helper._prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            global_section,
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'tagged'),
            ]),
            ('section3', [
                ('key1', 'value1'),
                ('key2', 'value2'),
                ('key3', 'value3'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'udp'),
            ]),
        ]

        result = setup_helper.global_section
        self.assertEqual(result, global_section[1])

    def test_find_in_section(self):
        setup_helper = ProxDpdkVnfSetupEnvHelper(mock.MagicMock(), mock.MagicMock(),
                                                 mock.MagicMock())

        setup_helper._prox_config_data = [
            ('global', [
                ('not_name', 'other data'),
                ('name_not', 'more data'),
                ('name', 'prox type'),
            ]),
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'tagged'),
            ]),
            ('section3', [
                ('key1', 'value1'),
                ('key2', 'value2'),
                ('key3', 'value3'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'udp'),
            ]),
        ]

        expected = 'value3'
        result = setup_helper.find_in_section('section3', 'key3')
        self.assertEqual(result, expected)

        expected = 'default value'
        result = setup_helper.find_in_section('section3', 'key4', 'default value')
        self.assertEqual(result, expected)

        with self.assertRaises(KeyError):
            setup_helper.find_in_section('section4', 'key1')

        with self.assertRaises(KeyError):
            setup_helper.find_in_section('section1', 'key1')

    def test__replace_quoted_with_value(self):
        # empty string
        input_str = ''
        expected = ''
        result = ProxDpdkVnfSetupEnvHelper._replace_quoted_with_value(input_str, 'cat')
        self.assertEqual(result, expected)

        # no quoted substring
        input_str = 'lion tiger bear'
        expected = 'lion tiger bear'
        result = ProxDpdkVnfSetupEnvHelper._replace_quoted_with_value(input_str, 'cat')
        self.assertEqual(result, expected)

        # partially quoted substring
        input_str = 'lion "tiger bear'
        expected = 'lion "tiger bear'
        result = ProxDpdkVnfSetupEnvHelper._replace_quoted_with_value(input_str, 'cat')
        self.assertEqual(result, expected)

        # one quoted substring
        input_str = 'lion "tiger" bear'
        expected = 'lion "cat" bear'
        result = ProxDpdkVnfSetupEnvHelper._replace_quoted_with_value(input_str, 'cat')
        self.assertEqual(result, expected)

        # two quoted substrings
        input_str = 'lion "tiger" bear "shark" whale'
        expected = 'lion "cat" bear "shark" whale'
        result = ProxDpdkVnfSetupEnvHelper._replace_quoted_with_value(input_str, 'cat')
        self.assertEqual(result, expected)

        # two quoted substrings, both replaced
        input_str = 'lion "tiger" bear "shark" whale'
        expected = 'lion "cat" bear "cat" whale'
        result = ProxDpdkVnfSetupEnvHelper._replace_quoted_with_value(input_str, 'cat', 2)
        self.assertEqual(result, expected)

    def test__get_tx_port(self):
        # no data
        input_data = {'section1': []}
        expected = -1
        result = ProxDpdkVnfSetupEnvHelper._get_tx_port('section1', input_data)
        self.assertEqual(result, expected)

        # data for other section
        input_data = {
            'section1': [],
            'section2': [
                ('rx port', '3'),
                ('tx port', '4'),
            ],
        }
        expected = -1
        result = ProxDpdkVnfSetupEnvHelper._get_tx_port('section1', input_data)
        self.assertEqual(result, expected)

        # data for section
        input_data['section1'] = section1 = [
            ('rx port', '4', 'more', 432),
            ('tx port', '3'),
        ]
        expected = 3
        result = ProxDpdkVnfSetupEnvHelper._get_tx_port('section1', input_data)
        self.assertEqual(result, expected)

        # more data for section,
        section1.extend([
            ('rx port', '2'),
            ('tx port', '1', 'and more', 234),
        ])
        expected = 1
        result = ProxDpdkVnfSetupEnvHelper._get_tx_port('section1', input_data)
        self.assertEqual(result, expected)

    # TODO(elfoley): Split this into several smaller tests
    def test_write_prox_config(self):
        input_data = {}
        expected = ''
        result = ProxDpdkVnfSetupEnvHelper.write_prox_config(input_data)
        self.assertEqual(result, expected)

        input_data = [
            [
                'section1',
                [],
            ],
        ]
        expected = '[section1]'
        result = ProxDpdkVnfSetupEnvHelper.write_prox_config(input_data)
        self.assertEqual(result, expected)

        input_data = [
            [
                'section1',
                [],
            ],
            [
                'section2',
                [
                    ['key1', 'value1'],
                    ['__name__', 'not this one'],
                    ['key2', None],
                    ['key3', 234],
                    ['key4', 'multi-line\nvalue'],
                ],
            ],
        ]
        expected = os.linesep.join([
            '[section1]',
            '[section2]',
            'key1=value1',
            'key2',
            'key3=234',
            'key4=multi-line\n\tvalue',
        ])
        result = ProxDpdkVnfSetupEnvHelper.write_prox_config(input_data)
        self.assertEqual(result, expected)

    def test_prox_config_data(self):
        setup_helper = ProxDpdkVnfSetupEnvHelper(mock.MagicMock(), mock.MagicMock(),
                                                 mock.MagicMock())

        setup_helper.config_queue = config_queue = mock.MagicMock()
        config_queue.get.return_value = expected = [('s', [('a', 3), ('b', 45)])]

        result = setup_helper.prox_config_data
        self.assertEqual(result, expected)

    @mock.patch.object(utils, 'find_relative_file')
    def test_build_config_file_no_additional_file(self, mock_find_path):
        vnf1 = {
            'prox_args': {'-c': ""},
            'prox_path': 'd',
            'prox_config': 'e/f',
            'prox_generate_parameter': False,
        }

        mock_find_path.side_effect = ['1', '2']

        vnfd_helper = mock.MagicMock()
        ssh_helper = mock.MagicMock()
        scenario_helper = ScenarioHelper('vnf1')
        scenario_helper.scenario_cfg = {
            'task_path': 'a/b',
            'options': {
                'vnf1': vnf1,
            },
        }

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.copy_to_target = mock.MagicMock(return_value='3')
        helper.generate_prox_config_file = mock.MagicMock(return_value='4')
        helper.upload_prox_config = mock.MagicMock(return_value='5')

        self.assertEqual(helper.additional_files, {})
        self.assertNotEqual(helper._prox_config_data, '4')
        self.assertNotEqual(helper.remote_path, '5')
        helper.build_config_file()
        self.assertEqual(helper.additional_files, {})
        self.assertEqual(helper._prox_config_data, '4')
        self.assertEqual(helper.remote_path, '5')

    @mock.patch.object(utils, 'find_relative_file')
    def test_build_config_file_additional_file_string(self, mock_find_path):
        vnf1 = {
            'prox_args': {'-c': ""},
            'prox_path': 'd',
            'prox_config': 'e/f',
            'prox_files': 'g/h.i',
            'prox_generate_parameter': True,
        }

        mock_find_path.side_effect = ['1', '2']
        vnfd_helper = mock.MagicMock()
        ssh_helper = mock.MagicMock()
        scenario_helper = ScenarioHelper('vnf1')
        scenario_helper.scenario_cfg = {
            'task_path': 'a/b',
            'options': {
                'vnf1': vnf1,
            },
        }

        vnfd_helper.port_pairs.all_ports = ['xe0', 'xe1', 'xe2', 'xe3']
        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.copy_to_target = mock.MagicMock(side_effect=['33', '34', '35'])
        helper.generate_prox_config_file = mock.MagicMock(return_value='44')
        helper.upload_prox_config = mock.MagicMock(return_value='55')

        self.assertEqual(helper.additional_files, {})
        expected = {'h.i': '33'}
        helper.build_config_file()
        self.assertDictEqual(helper.additional_files, expected)

    @mock.patch.object(utils, 'find_relative_file')
    def test_build_config_file_additional_file(self, mock_find_path):
        vnf1 = {
            'prox_args': {'-c': ""},
            'prox_path': 'd',
            'prox_config': 'e/f',
            'prox_files': [
                'g/h.i',
                'j/k/l',
                'm_n',
            ],
        }

        mock_find_path.side_effect = ['1', '2'] + [str(i) for i in range(len(vnf1['prox_files']))]
        vnfd_helper = mock.MagicMock()
        ssh_helper = mock.MagicMock()
        scenario_helper = ScenarioHelper('vnf1')
        scenario_helper.scenario_cfg = {
            'task_path': 'a/b',
            'options': {
                'vnf1': vnf1,
            },
        }

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.copy_to_target = mock.MagicMock(side_effect=['33', '34', '35'])
        helper.generate_prox_config_file = mock.MagicMock(return_value='44')
        helper.upload_prox_config = mock.MagicMock(return_value='55')

        self.assertEqual(helper.additional_files, {})
        self.assertNotEqual(helper._prox_config_data, '44')
        self.assertNotEqual(helper.remote_path, '55')
        expected = {'h.i': '33', 'l': '34', 'm_n': '35'}
        helper.build_config_file()
        self.assertDictEqual(helper.additional_files, expected)
        self.assertEqual(helper._prox_config_data, '44')
        self.assertEqual(helper.remote_path, '55')

    def test_build_config(self):
        vnf1 = {
            'prox_args': {'-f': ""},
            'prox_path': '/opt/nsb_bin/prox',
            'prox_config': 'configs/gen_l2fwd-2.cfg',
            'prox_files': [
                'g/h.i',
                'j/k/l',
                'm_n',
            ],
        }

        vnfd_helper = mock.Mock()
        ssh_helper = mock.Mock()
        ssh_helper.join_bin_path.return_value = '/opt/nsb_bin/prox'
        scenario_helper = ScenarioHelper('vnf1')
        scenario_helper.scenario_cfg = {
            'task_path': 'a/b',
            'options': {
                'vnf1': vnf1,
            },
        }

        expected = ("sudo bash -c 'cd /opt/nsb_bin; /opt/nsb_bin/prox -o cli "
                    "-f  -f /tmp/prox.cfg '")

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper,
                                           scenario_helper)
        with mock.patch.object(helper, 'build_config_file') as mock_cfg_file:
            helper.remote_path = '/tmp/prox.cfg'
            prox_cmd = helper.build_config()
            self.assertEqual(prox_cmd, expected)
            mock_cfg_file.assert_called_once()

    def test__insert_additional_file(self):
        vnfd_helper = mock.MagicMock()
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.MagicMock()

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.additional_files = {"ipv4.lua": "/tmp/ipv4.lua"}
        res = helper._insert_additional_file('dofile("ipv4.lua")')
        self.assertEqual(res, 'dofile("/tmp/ipv4.lua")')

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.ConfigParser')
    def test_generate_prox_config_file(self, mock_parser_type):
        def init(*args):
            if sections_data:
                args[-1].extend(sections_data)
            return mock.MagicMock()

        sections_data = []

        mock_parser_type.side_effect = init

        vnfd_helper = VnfdHelper(self.VNFD0)
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.MagicMock()

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.additional_files = {}

        expected = []
        result = helper.generate_prox_config_file('a/b')
        self.assertEqual(result, expected)

        helper.additional_files = {"ipv4.lua": "/tmp/ipv4.lua"}

        helper.remote_prox_file_name = 'remote'
        sections_data = [
            [
                'lua',
                [
                    ['dofile("ipv4.lua")', ''],
                ],
            ],
            [
                'port 0',
                [
                    ['ip', ''],
                    ['mac', 'foo'],
                    ['dst mac', '@@1'],
                    ['tx port', '1'],
                ],
            ],
            [
                'port 2',
                [
                    ['ip', ''],
                    ['$sut_mac0', '@@dst_mac0'],
                    ['tx port', '0'],
                    ['single', '@'],
                    ['user_table', 'dofile("ipv4.lua")'],
                    ['missing_addtional_file', 'dofile("nosuch")'],
                ],
            ],
        ]

        expected = [
            [
                'lua',
                [
                    ['dofile("/tmp/ipv4.lua")', ''],
                ],
            ],
            [
                'port 0',
                [
                    ['ip', ''],
                    ['mac', 'hardware'],
                    ['dst mac', '00:00:00:00:00:03'],
                    ['tx port', '1'],
                ],
            ],
            [
                'port 2',
                [
                    ['ip', ''],
                    ['$sut_mac0', '00 00 00 00 00 04'],
                    ['tx port', '0'],
                    ['single', '@'],
                    ['user_table', 'dofile("/tmp/ipv4.lua")'],
                    ['missing_addtional_file', 'dofile("nosuch")'],
                ],
            ],
        ]
        result = helper.generate_prox_config_file('/c/d/e')
        self.assertEqual(result, expected, str(result))

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.ConfigParser')
    def test_generate_prox_config_file_negative(self, mock_parser_type):
        def init(*args):
            args[-1].update(sections_data)
            return mock.MagicMock()

        sections_data = {}

        mock_parser_type.side_effect = init

        vnfd_helper = mock.MagicMock()
        vnfd_helper.interfaces = []
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.MagicMock()

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.additional_files = {}
        helper.remote_prox_file_name = 'remote'
        vnfd_helper.interfaces = [
            {
                'virtual-interface': {
                    'dpdk_port_num': 3,
                    'dst_mac': '00:00:00:de:ad:88',
                },
            },
            {
                'virtual-interface': {
                    'dpdk_port_num': 5,
                    'dst_mac': '00:00:00:de:ad:ff',
                },
            },
            {
                'virtual-interface': {
                    'dpdk_port_num': 7,
                    'dst_mac': '00:00:00:de:ad:ff',
                },
            },
        ]
        sections_data = {
            'port 3': [
                ['ip', ''],
                ['mac', 'foo'],
                ['dst mac', ''],
            ],
            'port 5': [
                ['ip', ''],
                ['dst mac', ''],
                ['tx port', '0'],
                ['???', 'dofile "here" 23'],
            ],
        }

        with self.assertRaises(Exception):
            helper.generate_prox_config_file('a/b')

    def test_put_string_to_file(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.interfaces = []
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.MagicMock()

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)

        expected = 'a/b'
        result = helper.put_string_to_file('my long string', 'a/b')
        self.assertEqual(result, expected)

    def test_copy_to_target(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.interfaces = []
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.MagicMock()

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        expected = '/tmp/c'
        result = helper.copy_to_target('a/b', 'c')
        self.assertEqual(result, expected)

    def test_upload_prox_config(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.interfaces = []
        ssh_helper = mock.MagicMock()
        scenario_helper = mock.MagicMock()

        helper = ProxDpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        helper.write_prox_config = mock.MagicMock(return_value='a long string')
        expected = '/tmp/a'
        result = helper.upload_prox_config('a', {})
        self.assertEqual(result, expected)


class TestProxResourceHelper(unittest.TestCase):

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

    def test_find_pci(self):
        input_str_list = [
            'no target here',
            'nor here',
            'and still not',
        ]
        result = ProxResourceHelper.find_pci('target', input_str_list)
        self.assertFalse(result)

        input_str_list = [
            'no target here',
            'nor here',
            'this is a target',
            'did we miss it',
        ]
        result = ProxResourceHelper.find_pci('target', input_str_list)
        self.assertTrue(result)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.RETRY_INTERVAL', 0)
    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.ProxSocketHelper')
    def test_sut(self, *args):
        helper = ProxResourceHelper(mock.MagicMock())
        self.assertIsNone(helper.client)
        result = helper.sut
        self.assertIsNotNone(result)
        self.assertIs(result, helper.client)
        self.assertIs(result, helper.sut)

    def test_test_type(self):
        setup_helper = mock.MagicMock()
        setup_helper.find_in_section.return_value = expected = 'prox type'

        helper = ProxResourceHelper(setup_helper)

        self.assertIsNone(helper._test_type)
        self.assertEqual(helper.test_type, expected)
        self.assertEqual(helper._test_type, expected)
        self.assertEqual(helper.test_type, expected)

    def test_collect_collectd_kpi(self):
        helper = ProxResourceHelper(mock.MagicMock())
        helper.resource = resource = mock.MagicMock()

        resource.check_if_system_agent_running.return_value = 0, '1234'
        resource.amqp_collect_nfvi_kpi.return_value = 543
        resource.check_if_system_agent_running.return_value = (0, None)

        expected = {'core': 543}
        result = helper.collect_collectd_kpi()
        self.assertDictEqual(result, expected)

    def test_collect_kpi(self):
        helper = ProxResourceHelper(mock.MagicMock())
        helper._queue = queue = mock.MagicMock()
        helper._result = {'z': 123}
        helper.resource = resource = mock.MagicMock()

        resource.check_if_system_agent_running.return_value = 0, '1234'
        resource.amqp_collect_nfvi_kpi.return_value = 543
        resource.check_if_system_agent_running.return_value = (0, None)

        queue.empty.return_value = False
        queue.get.return_value = {'a': 789}

        expected = {'z': 123, 'a': 789, 'collect_stats': {'core': 543}}
        result = helper.collect_kpi()
        self.assertDictEqual(result, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.ProxSocketHelper')
    def test__connect(self, mock_socket_helper_type, *args):
        client = mock_socket_helper_type()
        client.connect.side_effect = chain(repeat(socket.error, 5), [None])

        setup_helper = mock.MagicMock()
        setup_helper.vnfd_helper.interfaces = []

        helper = ProxResourceHelper(setup_helper)

        result = helper._connect()
        self.assertIs(result, client)

        client.connect.side_effect = chain(repeat(socket.error, 65), [None])

        with self.assertRaises(Exception):
            helper._connect()

    def test_run_traffic(self):
        setup_helper = mock.MagicMock()
        helper = ProxResourceHelper(setup_helper)
        traffic_profile = mock.MagicMock(**{"done": True})
        helper.run_traffic(traffic_profile)
        self.assertEqual(helper._terminated.value, 1)

    def test__run_traffic_once(self):
        setup_helper = mock.MagicMock()
        helper = ProxResourceHelper(setup_helper)
        traffic_profile = mock.MagicMock(**{"done": True})
        helper._run_traffic_once(traffic_profile)
        self.assertEqual(helper._terminated.value, 1)

    def test_start_collect(self):
        setup_helper = mock.MagicMock()
        helper = ProxResourceHelper(setup_helper)
        helper.resource = resource = mock.MagicMock()
        self.assertIsNone(helper.start_collect())
        resource.start.assert_called_once()

    def test_terminate(self):
        setup_helper = mock.MagicMock()
        helper = ProxResourceHelper(setup_helper)
        with self.assertRaises(NotImplementedError):
            helper.terminate()

    def test_up_post(self):
        setup_helper = mock.MagicMock()
        helper = ProxResourceHelper(setup_helper)
        helper.client = expected = mock.MagicMock()
        result = helper.up_post()
        self.assertEqual(result, expected)

    def test_execute(self):
        setup_helper = mock.MagicMock()
        helper = ProxResourceHelper(setup_helper)
        helper.client = mock.MagicMock()

        expected = helper.client.my_command()
        result = helper.execute('my_command')
        self.assertEqual(result, expected)

        # TODO(elfoley): Make this a separate test: test_execute_no_client
        helper.client = object()

        result = helper.execute('my_command')
        self.assertIsNone(result)


class TestProxDataHelper(unittest.TestCase):

    def test_totals_and_pps(self):
        pkt_size = 180
        vnfd_helper = mock.MagicMock()
        vnfd_helper.port_pairs.all_ports = list(range(4))

        sut = mock.MagicMock()
        sut.port_stats.return_value = list(range(10))

        data_helper = ProxDataHelper(
            vnfd_helper, sut, pkt_size, 25, None,
            constants.NIC_GBPS_DEFAULT * constants.ONE_GIGABIT_IN_BITS)

        self.assertEqual(data_helper.rx_total, 6)
        self.assertEqual(data_helper.tx_total, 7)
        self.assertEqual(data_helper.pps, 6.25e6)

    def test_samples(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.port_pairs.all_ports = list(range(4))
        vnfd_helper.ports_iter.return_value = [('xe1', 3), ('xe2', 7)]

        sut = mock.MagicMock()
        sut.port_stats.return_value = list(range(10))

        data_helper = ProxDataHelper(vnfd_helper, sut, None, None, None, None)

        expected = {
            'xe1': {
                'in_packets': 6,
                'out_packets': 7,
            },
            'xe2': {
                'in_packets': 6,
                'out_packets': 7,
            },
        }
        result = data_helper.samples
        self.assertDictEqual(result, expected)

    def test___enter__(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.port_pairs.all_ports = list(range(4))
        vnfd_helper.ports_iter.return_value = [('xe1', 3), ('xe2', 7)]

        sut = mock.MagicMock()
        sut.port_stats.return_value = list(range(10))

        data_helper = ProxDataHelper(vnfd_helper, sut, None, None,
            5.4, constants.NIC_GBPS_DEFAULT * constants.ONE_GIGABIT_IN_BITS)
        data_helper._totals_and_pps = 12, 32, 4.5
        data_helper.tsc_hz = 9.8
        data_helper.measured_stats = {'delta': TotStatsTuple(6.1, 6.2, 6.3, 6.4)}
        data_helper.latency = 7

        self.assertIsNone(data_helper.result_tuple)
        self.assertEqual(data_helper.line_speed, 10000000000)

        expected = ProxTestDataTuple(5.4, 9.8, 6.1, 6.2, 6.3, 7, 12, 32, 4.5)
        with data_helper:
            pass

        result = data_helper.result_tuple
        self.assertEqual(result, expected)

        data_helper.make_tuple()
        self.assertIs(data_helper.result_tuple, result)

    def test___enter___negative(self):
        vnfd_helper = mock.MagicMock()

        data_helper = ProxDataHelper(vnfd_helper, None, None, None, None, None)

        vnfd_helper.port_pairs.all_ports = []
        with self.assertRaises(AssertionError):
            with data_helper:
                pass

        vnfd_helper.port_pairs.all_ports = [0, 1, 2]
        with self.assertRaises(AssertionError):
            with data_helper:
                pass

    def test_measure_tot_stats(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.port_pairs.all_ports = list(range(4))

        start = (3, 4, 1, 2)
        end = (9, 7, 6, 8)

        sut = ProxSocketHelper(mock.MagicMock())
        sut.get_all_tot_stats = mock.MagicMock(side_effect=[start, end])

        data_helper = ProxDataHelper(vnfd_helper, sut, None, None, 5.4, None)

        self.assertIsNone(data_helper.measured_stats)

        expected = {
            'start_tot': start,
            'end_tot': end,
            'delta': TotStatsTuple(6, 3, 5, 6),
        }
        with data_helper.measure_tot_stats():
            pass

        self.assertEqual(data_helper.measured_stats, expected)

    def test_capture_tsc_hz(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.port_pairs.all_ports = list(range(4))

        sut = mock.MagicMock()
        sut.hz.return_value = '54.6'

        data_helper = ProxDataHelper(vnfd_helper, sut, None, None, None, None)

        self.assertIsNone(data_helper.tsc_hz)

        expected = 54.6
        data_helper.capture_tsc_hz()
        self.assertEqual(data_helper.tsc_hz, expected)


class TestProxProfileHelper(unittest.TestCase):

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.utils')
    def test_get_cls(self, mock_utils):
        mock_type1 = mock.MagicMock()
        mock_type1.__prox_profile_type__ = 'another_type'
        mock_type2 = mock.MagicMock()
        mock_type2.__prox_profile_type__ = 'my_type'
        mock_utils.itersubclasses.return_value = [mock_type1, mock_type2]

        self.assertEqual(ProxProfileHelper.get_cls('my_type'), mock_type2)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.utils')
    def test_get_cls_default(self, mock_utils):
        mock_utils.itersubclasses.return_value = []
        ProxProfileHelper.get_cls('my_type')

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.SocketTopology')
    def test_cpu_topology(self, mock_socket_topology):
        mock_socket_topology.parse_cpuinfo.return_value = 432

        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.ssh_helper.execute.return_value = 0, 'output', ''

        helper = ProxProfileHelper(resource_helper)
        self.assertIsNone(helper._cpu_topology)
        result = helper.cpu_topology
        self.assertEqual(result, 432)
        self.assertIs(result, helper._cpu_topology)
        self.assertIs(result, helper.cpu_topology)

    # TODO(elfoley): Split this test; there are two sets of inputs/outputs
    def test_test_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = []

        helper = ProxProfileHelper(resource_helper)
        helper._cpu_topology = []

        expected = []
        result = helper.test_cores
        self.assertEqual(result, expected)

        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1s3', []),
            ('core 2s5', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3s1', [
                ('index', 5),
                ('mode', 'gen'),
            ]),
            ('core 4s9h', [
                ('index', 7),
                ('mode', 'gen'),
            ]),
        ]

        helper = ProxProfileHelper(resource_helper)
        helper._cpu_topology = {
            1: {
                3: {
                    'key1': (23, 32),
                    'key2': (12, 21),
                    'key3': (44, 33),
                },
            },
            9: {
                4: {
                    'key1': (44, 32),
                    'key2': (23, 21),
                    'key3': (12, 33),
                },
            },
        }

        self.assertIsNone(helper._test_cores)
        expected = [3, 4]
        result = helper.test_cores
        self.assertEqual(result, expected)
        self.assertIs(result, helper._test_cores)
        self.assertIs(result, helper.test_cores)

    # TODO(elfoley): Split this test; there are two sets of inputs/outputs
    def test_latency_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = []

        helper = ProxProfileHelper(resource_helper)
        helper._cpu_topology = []

        expected = []
        result = helper.latency_cores
        self.assertEqual(result, expected)

        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1s3', []),
            ('core 2s5', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3s1', [
                ('index', 5),
                ('mode', 'lat'),
            ]),
            ('core 4s9h', [
                ('index', 7),
                ('mode', 'lat'),
            ]),
        ]

        helper = ProxProfileHelper(resource_helper)
        helper._cpu_topology = {
            1: {
                3: {
                    'key1': (23, 32),
                    'key2': (12, 21),
                    'key3': (44, 33),
                },
            },
            9: {
                4: {
                    'key1': (44, 32),
                    'key2': (23, 21),
                    'key3': (12, 33),
                },
            },
        }

        self.assertIsNone(helper._latency_cores)
        expected = [3, 4]
        result = helper.latency_cores
        self.assertEqual(result, expected)
        self.assertIs(result, helper._latency_cores)
        self.assertIs(result, helper.latency_cores)

    def test_all_rx_cores(self):
        helper = ProxBngProfileHelper(mock.MagicMock())
        helper._latency_cores = expected = [3, 4, 6]
        helper._test_cores = [5, 2, 1]

        result = helper.all_rx_cores
        self.assertEqual(result, expected)

    def test_get_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
            ]),
        ]

        helper = ProxProfileHelper(resource_helper)
        helper._cpu_topology = {
            0: {
                1: {
                    5: (5, 1, 0)
                },
                2: {
                    6: (6, 2, 0)
                },
                3: {
                    7: (7, 3, 0)
                },
                4: {
                    8: (8, 3, 0)
                },
            }
        }

        expected = [3, 4]
        result = helper.get_cores(helper.PROX_CORE_GEN_MODE)
        self.assertEqual(result, expected)

    def test_get_latency(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.vnfd_helper.interfaces = []

        helper = ProxProfileHelper(resource_helper)
        helper._latency_cores = []

        expected = []
        result = helper.get_latency()
        self.assertEqual(result, expected)

        helper._latency_cores = [1, 2]
        helper.client = mock.MagicMock()

        expected = helper.sut.lat_stats()
        result = helper.get_latency()
        self.assertIs(result, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
    def test_traffic_context(self, *args):
        setup_helper = mock.MagicMock()
        setup_helper.vnfd_helper.interfaces = []

        helper = ProxProfileHelper(setup_helper)
        helper._cpu_topology = {
            0: {
                1: {
                    5: (5, 1, 0)
                },
                2: {
                    6: (6, 2, 0)
                },
                3: {
                    7: (7, 3, 0)
                },
                4: {
                    8: (8, 3, 0)
                },
            }
        }

        setup_helper.prox_config_data = [
            ('global', [
                ('not_name', 'other data'),
                ('name_not', 'more data'),
                ('name', helper.__prox_profile_type__),
            ]),
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'tagged'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'udp'),
            ]),
        ]

        client = mock.MagicMock()
        client.hz.return_value = 2
        client.port_stats.return_value = tuple(range(12))

        helper.client = client
        helper.get_latency = mock.MagicMock(return_value=[3.3, 3.6, 3.8])

        helper._test_cores = [3, 4]

        with helper.traffic_context(64, 1):
            pass

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
    def test_run_test(self, _):
        resource_helper = mock.MagicMock()
        resource_helper.step_delta = 0.4
        resource_helper.vnfd_helper.port_pairs.all_ports = list(range(2))
        resource_helper.sut.port_stats.return_value = list(range(10))

        helper = ProxProfileHelper(resource_helper)

        helper.run_test(120, 5, 6.5,
                        constants.NIC_GBPS_DEFAULT * constants.ONE_GIGABIT_IN_BITS)


class TestProxMplsProfileHelper(unittest.TestCase):

    def test_mpls_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'tagged'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'udp'),
            ]),
        ]

        helper = ProxMplsProfileHelper(resource_helper)
        helper._cpu_topology = {
            0: {
                1: {
                    5: (5, 1, 0)
                },
                2: {
                    6: (6, 2, 0)
                },
                3: {
                    7: (7, 3, 0)
                },
                4: {
                    8: (8, 3, 0)
                },
            }
        }

        expected_tagged = [3]
        expected_plain = [4]
        self.assertIsNone(helper._cores_tuple)
        self.assertEqual(helper.tagged_cores, expected_tagged)
        self.assertEqual(helper.plain_cores, expected_plain)
        self.assertEqual(helper._cores_tuple, (expected_tagged, expected_plain))

    def test_traffic_context(self):
        setup_helper = mock.MagicMock()
        helper = ProxMplsProfileHelper(setup_helper)

        with helper.traffic_context(120, 5.4):
            pass


class TestProxBngProfileHelper(unittest.TestCase):

    def test_bng_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'cpe'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'inet'),
            ]),
            ('core 6', [
                ('index', 3),
                ('mode', 'gen'),
                ('name', 'arp_task'),
            ]),
            ('core 9', [
                ('index', 2),
                ('mode', 'gen'),
                ('name', 'arp'),
            ]),
        ]

        helper = ProxBngProfileHelper(resource_helper)
        helper._cpu_topology = {
            0: {
                1: {
                    5: (5, 1, 0)
                },
                2: {
                    6: (6, 2, 0)
                },
                3: {
                    7: (7, 3, 0)
                },
                4: {
                    8: (8, 3, 0)
                },
                6: {
                    1: (4, 8, 0)
                },
                9: {
                    2: (3, 7, 0)
                },
            }
        }

        expected_cpe = [3]
        expected_inet = [4]
        expected_arp = [6, 9]
        expected_arp_task = [0, 6]
        expected_combined = (expected_cpe, expected_inet, expected_arp, expected_arp_task)

        self.assertIsNone(helper._cores_tuple)
        self.assertEqual(helper.cpe_cores, expected_cpe)
        self.assertEqual(helper.inet_cores, expected_inet)
        self.assertEqual(helper.arp_cores, expected_arp)
        self.assertEqual(helper.arp_task_cores, expected_arp_task)
        self.assertEqual(helper._cores_tuple, expected_combined)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
    def test_run_test(self, _):
        resource_helper = mock.MagicMock()
        resource_helper.step_delta = 0.4
        resource_helper.vnfd_helper.port_pairs.all_ports = list(range(2))
        resource_helper.sut.port_stats.return_value = list(range(10))

        helper = ProxBngProfileHelper(resource_helper)

        helper.run_test(120, 5, 6.5,
                        constants.NIC_GBPS_DEFAULT * constants.ONE_GIGABIT_IN_BITS)

        # negative pkt_size is the only way to make ratio > 1
        helper.run_test(-1000, 5, 6.5,
                        constants.NIC_GBPS_DEFAULT * constants.ONE_GIGABIT_IN_BITS)


class TestProxVpeProfileHelper(unittest.TestCase):

    def test_vpe_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'cpe'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'inet'),
            ]),
        ]

        helper = ProxVpeProfileHelper(resource_helper)
        helper._cpu_topology = {
            0: {
                1: {
                    5: (5, 1, 0)
                },
                2: {
                    6: (6, 2, 0)
                },
                3: {
                    7: (7, 3, 0)
                },
                4: {
                    8: (8, 3, 0)
                },
            }
        }

        expected_cpe = [3]
        expected_inet = [4]
        expected_combined = (expected_cpe, expected_inet)

        self.assertIsNone(helper._cores_tuple)
        self.assertEqual(helper.cpe_cores, expected_cpe)
        self.assertEqual(helper.inet_cores, expected_inet)
        self.assertEqual(helper._cores_tuple, expected_combined)

    def test_vpe_ports(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('port 3', [
                ('index', '5'),
                ('name', 'cpe'),
                ('mac', 'hardware'),
            ]),
            ('port 4', [
                ('index', '7'),
                ('name', 'inet'),
                ('mac', 'hardware'),
            ]),
        ]

        helper = ProxVpeProfileHelper(resource_helper)
        helper._port_list = {
            0: {
                1: {
                    5: 'cpe'
                },
                2: {
                    6: 'inet'
                },
                3: {
                    7: 'cpe'
                },
                4: {
                    8: 'inet'
                },
            }
        }

        expected_cpe = [3]
        expected_inet = [4]
        expected_combined = (expected_cpe, expected_inet)

        self.assertIsNone(helper._ports_tuple)
        self.assertEqual(helper.cpe_ports, expected_cpe)
        self.assertEqual(helper.inet_ports, expected_inet)
        self.assertEqual(helper._ports_tuple, expected_combined)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
    def test_run_test(self, _):
        resource_helper = mock.MagicMock()
        resource_helper.step_delta = 0.4
        resource_helper.vnfd_helper.port_pairs.all_ports = list(range(2))
        resource_helper.sut.port_stats.return_value = list(range(10))

        helper = ProxVpeProfileHelper(resource_helper)

        helper.run_test(120, 5, 6.5)
        helper.run_test(-1000, 5, 6.5)  # negative pkt_size is the only way to make ratio > 1


class TestProxlwAFTRProfileHelper(unittest.TestCase):

    def test_lwaftr_cores(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('core 1', []),
            ('core 2', [
                ('index', 8),
                ('mode', ''),
            ]),
            ('core 3', [
                ('index', 5),
                ('mode', 'gen'),
                ('name', 'tun'),
            ]),
            ('core 4', [
                ('index', 7),
                ('mode', 'gen'),
                ('name', 'inet'),
            ]),
        ]

        helper = ProxlwAFTRProfileHelper(resource_helper)
        helper._cpu_topology = {
            0: {
                1: {
                    5: (5, 1, 0)
                },
                2: {
                    6: (6, 2, 0)
                },
                3: {
                    7: (7, 3, 0)
                },
                4: {
                    8: (8, 3, 0)
                },
            }
        }

        expected_tun = [3]
        expected_inet = [4]
        expected_combined = (expected_tun, expected_inet)

        self.assertIsNone(helper._cores_tuple)
        self.assertEqual(helper.tun_cores, expected_tun)
        self.assertEqual(helper.inet_cores, expected_inet)
        self.assertEqual(helper._cores_tuple, expected_combined)

    def test_tun_ports(self):
        resource_helper = mock.MagicMock()
        resource_helper.setup_helper.prox_config_data = [
            ('section1', []),
            ('section2', [
                ('a', 'b'),
                ('c', 'd'),
            ]),
            ('port 3', [
                ('index', '5'),
                ('name', 'lwB4'),
                ('mac', 'hardware'),
            ]),
            ('port 4', [
                ('index', '7'),
                ('name', 'inet'),
                ('mac', 'hardware'),
            ]),
        ]

        helper = ProxlwAFTRProfileHelper(resource_helper)
        helper._port_list = {
            0: {
                1: {
                    5: 'lwB4'
                },
                2: {
                    6: 'inet'
                },
                3: {
                    7: 'lwB4'
                },
                4: {
                    8: 'inet'
                },
            }
        }

        expected_tun = [3]
        expected_inet = [4]
        expected_combined = (expected_tun, expected_inet)

        self.assertIsNone(helper._ports_tuple)
        self.assertEqual(helper.tun_ports, expected_tun)
        self.assertEqual(helper.inet_ports, expected_inet)
        self.assertEqual(helper._ports_tuple, expected_combined)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
    def test_run_test(self, _):
        resource_helper = mock.MagicMock()
        resource_helper.step_delta = 0.4
        resource_helper.vnfd_helper.port_pairs.all_ports = list(range(2))
        resource_helper.sut.port_stats.return_value = list(range(10))

        helper = ProxlwAFTRProfileHelper(resource_helper)

        helper.run_test(120, 5, 6.5)
        helper.run_test(-1000, 5, 6.5)  # negative pkt_size is the only way to make ratio > 1
