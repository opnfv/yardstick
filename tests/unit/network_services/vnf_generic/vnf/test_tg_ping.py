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
from multiprocessing import Queue

from tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh

SSH_HELPER = "yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper"

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
    from yardstick.network_services.vnf_generic.vnf.tg_ping import PingParser, PingTrafficGen
    from yardstick.network_services.traffic_profile.base import TrafficProfile
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import VnfSshHelper


class TestPingParser(unittest.TestCase):
    def test___init__(self):
        q_out = Queue()
        ping_parser = PingParser(q_out)
        self.assertIsNotNone(ping_parser.queue)

    def test_clear(self):
        sample_out = """
64 bytes from 10.102.22.93: icmp_seq=3 ttl=64 time=0.296 ms
         """
        q_out = Queue()
        ping_parser = PingParser(q_out)
        ping_parser.write(sample_out)
        ping_parser.clear()
        self.assertEqual(True, q_out.empty())

    def test_close(self):
        q_out = Queue()
        ping_parser = PingParser(q_out)
        self.assertIsNone(ping_parser.close())

    def test_write(self):
        sample_out = """
64 bytes from 10.102.22.93: icmp_seq=3 ttl=64 time=0.296 ms
         """
        q_out = Queue()
        ping_parser = PingParser(q_out)
        ping_parser.write(sample_out)

        self.assertEqual({"packets_received": 3.0, "rtt": 0.296}, q_out.get())


class TestPingTrafficGen(unittest.TestCase):

    VNFD_0_EXT_IF_0 = {
        'virtual-interface': {
            'dst_mac': '00:00:00:00:00:04',
            'vpci': '0000:05:00.0',
            'local_ip': u'152.16.100.19',
            'type': 'PCI-PASSTHROUGH',
            'netmask': '255.255.255.0',
            'dpdk_port_num': '0',
            'bandwidth': '10 Gbps',
            'driver': "i40e",
            'dst_ip': u'152.16.100.20',
            'local_iface_name': 'xe0',
            'local_mac': '00:00:00:00:00:02',
        },
        'vnfd-connection-point-ref': 'xe0',
        'name': 'xe0',
    }

    VNFD_0_EXT_IF_1 = {
        'virtual-interface': {
            'dst_mac': '00:00:00:00:00:03',
            'vpci': '0000:05:00.1',
            'local_ip': u'152.16.40.19',
            'type': 'PCI-PASSTHROUGH',
            'driver': "i40e",
            'netmask': '255.255.255.0',
            'dpdk_port_num': '1',
            'bandwidth': '10 Gbps',
            'dst_ip': u'152.16.40.20',
            'local_iface_name': 'xe1',
            'local_mac': '00:00:00:00:00:01',
        },
       'vnfd-connection-point-ref': 'xe1',
       'name': 'xe1',
    }

    VNFD_0_EXT_IF_LIST = [
        VNFD_0_EXT_IF_0,
        VNFD_0_EXT_IF_1,
    ]

    VNFD_0 = {
        'short-name': 'VpeVnf',
        'vdu': [
            {
                'routing_table': [
                    {
                        'network': u'152.16.100.20',
                        'netmask': u'255.255.255.0',
                        'gateway': u'152.16.100.20',
                        'if': 'xe0',
                    },
                    {
                        'network': u'152.16.40.20',
                        'netmask': u'255.255.255.0',
                        'gateway': u'152.16.40.20',
                        'if': 'xe1',
                    },
                ],
                'description': 'VPE approximation using DPDK',
                'name': 'vpevnf-baremetal',
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
                'id': 'vpevnf-baremetal',
                'external-interface': VNFD_0_EXT_IF_LIST,
            },
        ],
        'description': 'Vpe approximation using DPDK',
        'mgmt-interface': {
        'vdu-id': 'vpevnf-baremetal',
            'host': '1.1.1.1',
            'password': 'r00t',
            'user': 'root',
            'ip': '1.1.1.1',
        },
        'benchmark': {
            'kpi': [
                'packets_in',
                'packets_fwd',
                'packets_dropped',
            ],
        },
        'connection-point': [
            {
                'type': 'VPORT',
                'name': 'xe0',
            },
            {
                'type': 'VPORT',
                'name': 'xe1',
            },
        ],
        'id': 'VpeApproxVnf',
        'name': 'VPEVnfSsh',
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ],
        },
    }

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

    @mock.patch("yardstick.ssh.SSH")
    def test___init__(self, ssh):
        ssh.from_node.return_value.execute.return_value = 0, "success", ""
        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        self.assertIsNotNone(ping_traffic_gen._queue)

    @mock.patch("yardstick.ssh.SSH")
    def test__bind_device_kernel_with_failure(self, ssh):
        mock_ssh(ssh)

        execute_result_data = [
            (1, 'bad stdout messages', 'error messages'),
            (0, '', ''),
            (0, 'if_name_1', ''),
            (0, 'if_name_2', ''),
        ]
        ssh.from_node.return_value.execute.side_effect = iter(execute_result_data)
        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        ext_ifs = ping_traffic_gen.vnfd_helper.interfaces
        self.assertNotEqual(ext_ifs[0]['virtual-interface']['local_iface_name'], 'if_name_1')
        self.assertNotEqual(ext_ifs[1]['virtual-interface']['local_iface_name'], 'if_name_2')

    @mock.patch("yardstick.ssh.SSH")
    def test_collect_kpi(self, ssh):
        mock_ssh(ssh, exec_result=(0, "success", ""))
        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        ping_traffic_gen._queue = Queue()
        ping_traffic_gen._queue.put({})
        ping_traffic_gen.collect_kpi()
        self.assertEqual(ping_traffic_gen._result, {})

    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh):
        mock_ssh(ssh, spec=VnfSshHelper, exec_result=(0, "success", ""))
        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        ping_traffic_gen.setup_helper.ssh_helper = mock.MagicMock(
            **{"execute.return_value": (0, "", "")})
        self.assertIsInstance(ping_traffic_gen.ssh_helper, mock.Mock)
        self.assertEqual(ping_traffic_gen._result, {})
        self.assertIsNone(ping_traffic_gen.instantiate({}, {}))
        self.assertIsNotNone(ping_traffic_gen._result)

    @mock.patch("yardstick.ssh.SSH")
    def test_listen_traffic(self, ssh):
        ssh.from_node.return_value.execute.return_value = 0, "success", ""
        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        self.assertIsNone(ping_traffic_gen.listen_traffic({}))

    @mock.patch(SSH_HELPER)
    def test_run_traffic_process(self, ssh):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        ssh.from_node.return_value.execute.return_value = 0, "success", ""
        ssh.from_node.return_value.run.return_value = 0, "success", ""

        sut = PingTrafficGen('vnf1', self.VNFD_0)
        sut._traffic_runner(mock_traffic_profile)
        sut.ssh_helper.run.assert_called_with(
            "ping -s 64 152.16.100.20",
            stdout=sut._parser, keep_stdin_open=True, pty=True)

    @mock.patch("yardstick.ssh.SSH")
    def test_scale_negative(self, ssh):
        ssh.from_node.return_value.execute.return_value = 0, "success", ""
        ssh.from_node.return_value.run.return_value = 0, "success", ""

        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        ping_traffic_gen.scale()

    @mock.patch("yardstick.ssh.SSH")
    def test_terminate(self, ssh):
        ssh.from_node.return_value.execute.return_value = 0, "success", ""
        ssh.from_node.return_value.run.return_value = 0, "success", ""

        ping_traffic_gen = PingTrafficGen('vnf1', self.VNFD_0)
        self.assertIsNone(ping_traffic_gen.terminate())