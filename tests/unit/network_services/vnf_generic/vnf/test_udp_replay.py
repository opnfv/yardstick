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
import os

SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'

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
    from yardstick.network_services.vnf_generic.vnf.udp_replay import UdpReplayApproxVnf
    from yardstick.network_services.vnf_generic.vnf import udp_replay
    from yardstick.network_services.nfvi.resource import ResourceProfile

from tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh

TEST_FILE_YAML = 'nsb_test_case.yaml'


NAME = "tg__1"


@mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Process")
class TestUdpReplayApproxVnf(unittest.TestCase):

    VNFD_0 = {
        'short-name': 'UdpReplayVnf',
        'vdu': [
            {
                'description': 'UDPReplay approximation using DPDK',
                'routing_table': [
                    {
                        'netmask': '255.255.255.0',
                        'if': 'xe0',
                        'network': '152.16.100.20',
                        'gateway': '152.16.100.20',
                    },
                    {
                        'netmask': '255.255.255.0',
                        'if': 'xe1',
                        'network': '152.16.40.20',
                        'gateway': '152.16.40.20',
                    }
                ],
                'external-interface': [
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'driver': 'i40e',
                            'local_iface_name': 'xe0',
                            'bandwidth': '10 Gbps',
                            'local_ip': '152.16.100.19',
                            'local_mac': '00:00:00:00:00:02',
                            'vpci': '0000:05:00.0',
                            'dpdk_port_num': '0',
                            'netmask': '255.255.255.0',
                            'dst_ip': '152.16.100.20',
                            'type': 'PCI-PASSTHROUGH',
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0',
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:03',
                            'driver': 'i40e',
                            'local_iface_name': 'xe1',
                            'bandwidth': '10 Gbps',
                            'local_ip': '152.16.40.19',
                            'local_mac': '00:00:00:00:00:01',
                            'vpci': '0000:05:00.1',
                            'dpdk_port_num': '1',
                            'netmask': '255.255.255.0',
                            'dst_ip': '152.16.40.20',
                            'type': 'PCI-PASSTHROUGH',
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1',
                    }
                ],
                'nd_route_tbl': [
                    {
                        'netmask': '112',
                        'if': 'xe0',
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                    },
                    {
                        'netmask': '112',
                        'if': 'xe1',
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                    }
                ],
                'id': 'udpreplayvnf-baremetal',
                'name': 'udpreplayvnf-baremetal',
            }
        ],
        'description': 'UDPReplay approximation using DPDK',
        'name': 'VPEVnfSsh',
        'mgmt-interface': {
            'vdu-id': 'udpreplay-baremetal',
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
            ]
        },
        'connection-point': [
            {
                'type': 'VPORT',
                'name': 'xe0',
            },
            {
                'type': 'VPORT',
                'name': 'xe1',
            }
        ],
        'id': 'UdpReplayApproxVnf',
    }

    SCENARIO_CFG = {
        "options": {
            "packetsize": 64,
            "traffic_type": 4,
            "rfc2544": {
                "allowed_drop_rate": "0.8 - 1",
            },
            "vnf__1": {
                "rules": "acl_1rule.yaml",
                "vnf_config": {
                    "lb_config": "SW",
                    "lb_count": 1,
                    "worker_config": "1C/1T",
                    "worker_threads": 1,
                }
            }
        },
        "task_id": "a70bdf4a-8e67-47a3-9dc1-273c14506eb7",
        "tc": "tc_ipv4_1Mflow_64B_packetsize",
        "runner": {
            "object": "NetworkServiceTestCase",
            "interval": 35,
            "output_filename": "/tmp/yardstick.out",
            "runner_id": 74476, "duration": 400,
            "type": "Duration"
        },
        "traffic_profile": "ipv4_throughput_acl.yaml",
        "traffic_options": {
            "flow": "ipv4_Packets_acl.yaml",
            "imix": "imix_voice.yaml"
        },
        "type": "ISB",
        "nodes": {
            "tg__2": "trafficgen_2.yardstick",
            "tg__1": "trafficgen_1.yardstick",
            "vnf__1": "vnf.yardstick"
        },
        "topology": "udpreplay-tg-topology-baremetal.yaml"
    }

    CONTEXT_CFG = {
        "nodes": {
            "vnf__1": {
                "vnfd-id-ref": "vnf__1",
                "ip": "1.2.1.1",
                "interfaces": {
                    "xe0": {
                        "local_iface_name": "ens786f0",
                        "vld_id": "private",
                        "netmask": "255.255.255.0",
                        "vpci": "0000:05:00.0",
                        "local_ip": "152.16.100.19",
                        "driver": "i40e",
                        "dst_ip": "152.16.100.20",
                        "local_mac": "00:00:00:00:00:02",
                        "dst_mac": "00:00:00:00:00:04",
                        "dpdk_port_num": 0
                    },
                    "xe1": {
                        "local_iface_name": "ens786f1",
                        "vld_id": "public",
                        "netmask": "255.255.255.0",
                        "vpci": "0000:05:00.1",
                        "local_ip": "152.16.40.19",
                        "driver": "i40e",
                        "dst_ip": "152.16.40.20",
                        "local_mac": "00:00:00:00:00:01",
                        "dst_mac": "00:00:00:00:00:03",
                        "dpdk_port_num": 1
                    }
                },
                "host": "1.2.1.1",
                "user": "root",
                "nd_route_tbl": [
                    {
                        "netmask": "112",
                        "if": "xe0",
                        "gateway": "0064:ff9b:0:0:0:0:9810:6414",
                        "network": "0064:ff9b:0:0:0:0:9810:6414"
                    },
                    {
                        "netmask": "112",
                        "if": "xe1",
                        "gateway": "0064:ff9b:0:0:0:0:9810:2814",
                        "network": "0064:ff9b:0:0:0:0:9810:2814"
                    }
                ],
                "password": "r00t",
                "VNF model": "udp_replay.yaml",
                "name": "vnf.yardstick",
                "member-vnf-index": "2",
                "routing_table": [
                    {
                        "netmask": "255.255.255.0",
                        "if": "xe0",
                        "gateway": "152.16.100.20",
                        "network": "152.16.100.20"
                    },
                    {
                        "netmask": "255.255.255.0",
                        "if": "xe1",
                        "gateway": "152.16.40.20",
                        "network": "152.16.40.20"
                    }
                ],
                "role": "vnf"
            },
            "trafficgen_2.yardstick": {
                "member-vnf-index": "3",
                "role": "TrafficGen",
                "name": "trafficgen_2.yardstick",
                "vnfd-id-ref": "tg__2",
                "ip": "1.2.1.1",
                "interfaces": {
                    "xe0": {
                        "local_iface_name": "ens513f0",
                        "vld_id": "public",
                        "netmask": "255.255.255.0",
                        "vpci": "0000:02:00.0",
                        "local_ip": "152.16.40.20",
                        "driver": "ixgbe",
                        "dst_ip": "152.16.40.19",
                        "local_mac": "00:00:00:00:00:03",
                        "dst_mac": "00:00:00:00:00:01",
                        "dpdk_port_num": 0
                    },
                    "xe1": {
                        "local_iface_name": "ens513f1",
                        "netmask": "255.255.255.0",
                        "network": "202.16.100.0",
                        "local_ip": "202.16.100.20",
                        "driver": "ixgbe",
                        "local_mac": "00:1e:67:d0:60:5d",
                        "vpci": "0000:02:00.1",
                        "dpdk_port_num": 1
                    }
                },
                "password": "r00t",
                "VNF model": "l3fwd_vnf.yaml",
                "user": "root"
            },
            "trafficgen_1.yardstick": {
                "member-vnf-index": "1",
                "role": "TrafficGen",
                "name": "trafficgen_1.yardstick",
                "vnfd-id-ref": "tg__1",
                "ip": "1.2.1.1",
                "interfaces": {
                    "xe0": {
                        "local_iface_name": "ens785f0",
                        "vld_id": "private",
                        "netmask": "255.255.255.0",
                        "vpci": "0000:05:00.0",
                        "local_ip": "152.16.100.20",
                        "driver": "i40e",
                        "dst_ip": "152.16.100.19",
                        "local_mac": "00:00:00:00:00:04",
                        "dst_mac": "00:00:00:00:00:02",
                        "dpdk_port_num": 0
                    },
                    "xe1": {
                        "local_ip": "152.16.100.21",
                        "driver": "i40e",
                        "vpci": "0000:05:00.1",
                        "dpdk_port_num": 1,
                        "local_iface_name": "ens785f1",
                        "netmask": "255.255.255.0",
                        "local_mac": "00:00:00:00:00:01"
                    }
                },
                "password": "r00t",
                "VNF model": "tg_rfc2544_tpl.yaml",
                "user": "root"
            }
        }
    }

    def test___init__(self, _):
        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        self.assertIsNone(udp_approx_vnf._vnf_process)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, mock_time, _):
        mock_ssh(ssh)

        vnfd = self.VNFD_0
        result = "stats\r\r\n\r\nUDP_Replay stats:\r\n--------------\r\n" \
            "Port\t\tRx Packet\t\tTx Packet\t\tRx Pkt Drop\t\tTx Pkt Drop \r\n"\
            "0\t\t7374156\t\t7374136\t\t\t0\t\t\t0\r\n" \
            "1\t\t7374316\t\t7374315\t\t\t0\t\t\t0\r\n\r\nReplay>\r\r\nReplay>"
        udp_approx_vnf = UdpReplayApproxVnf(NAME, vnfd)
        udp_approx_vnf.q_in = mock.MagicMock()
        udp_approx_vnf.q_out = mock.MagicMock()
        udp_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        udp_approx_vnf.all_ports = [0, 1]
        udp_approx_vnf.interfaces = vnfd["vdu"][0]['external-interface']
        udp_approx_vnf.get_stats = mock.Mock(return_value=result)
        result = {'collect_stats': {}, 'packets_dropped': 0,
                    'packets_fwd': 14748451, 'packets_in': 14748472}
        self.assertEqual(result, udp_approx_vnf.collect_kpi())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_vnf_execute_command(self, ssh, mock_time, _):
        mock_ssh(ssh)

        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        cmd = "quit"
        self.assertEqual("", udp_approx_vnf.vnf_execute(cmd))

    @mock.patch(SSH_HELPER)
    def test_get_stats(self, ssh, _):
        mock_ssh(ssh)

        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_approx_vnf.q_in = mock.MagicMock()
        udp_approx_vnf.q_out = mock.MagicMock()
        udp_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        mock_result = \
            "CG-NAPT(.*\n)*Received 100, Missed 0, Dropped 0,Translated 100,ingress"
        udp_approx_vnf.vnf_execute = mock.Mock(return_value=mock_result)
        self.assertEqual(mock_result,
                            udp_approx_vnf.get_stats())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch('yardstick.network_services.vnf_generic.vnf.udp_replay.open')
    @mock.patch(SSH_HELPER)
    def test__build_pipeline_kwargs(self, ssh, mock_open, mock_context, _):
        mock_ssh(ssh)
        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_approx_vnf._build_config = mock.MagicMock()
        udp_approx_vnf.queue_wrapper = mock.MagicMock()
        udp_approx_vnf.nfvi_context = mock_context
        udp_approx_vnf.nfvi_context.attrs = {'nfvi_type': 'baremetal'}
        udp_approx_vnf.setup_helper.bound_pci = []
        udp_approx_vnf.all_ports = [0, 1]
        udp_approx_vnf.ssh_helper.provision_tool = mock.MagicMock(return_value="tool_path")
        udp_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                    'lb_count': 1,
                                    'worker_config': '1C/1T',
                                    'worker_threads': 1}
        udp_approx_vnf.options = {'traffic_type': '4',
                                    'topology': 'nsb_test_case.yaml'}

        udp_approx_vnf._build_pipeline_kwargs()
        self.assertEqual(udp_approx_vnf.pipeline_kwargs, {
            'config': '(0, 0, 1)(1, 0, 2)',
            'cpu_mask_hex': '0x7',
            'hw_csum': '',
            'ports_len_hex': '0x3',
            'tool_path': 'tool_path',
            'whitelist': ''
        })

    @mock.patch("yardstick.network_services.vnf_generic.vnf.udp_replay.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.udp_replay.eval")
    @mock.patch('yardstick.network_services.vnf_generic.vnf.udp_replay.open')
    @mock.patch(SSH_HELPER)
    def test_run_udp_replay(self, ssh, mock_open, eval, hex, _):
        mock_ssh(ssh)

        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_approx_vnf._build_config = mock.MagicMock()
        udp_approx_vnf.queue_wrapper = mock.MagicMock()
        udp_approx_vnf.ssh_helper = mock.MagicMock()
        udp_approx_vnf.ssh_helper.run = mock.MagicMock()
        udp_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                    'lb_count': 1,
                                    'worker_config': '1C/1T',
                                    'worker_threads': 1}
        udp_approx_vnf.options = {'traffic_type': '4',
                                    'topology': 'nsb_test_case.yaml'}

        udp_approx_vnf._run()
        udp_approx_vnf.ssh_helper.run.assert_called_once()

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, Context, _):
        mock_ssh(ssh)

        resource = mock.Mock(autospec=ResourceProfile)
        resource.check_if_sa_running.return_value = True, 'good'
        resource.amqp_collect_nfvi_kpi.return_value = {'foo': 234}

        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'cgnapt': {'cfg': "",
                                                        'rules': ""}}
        udp_approx_vnf._run_udp_replay = mock.Mock(return_value=0)
        udp_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        udp_approx_vnf.deploy_udp_replay_vnf = mock.Mock(return_value=1)
        udp_approx_vnf.q_out.put("Replay>")
        udp_approx_vnf._set_all_ports = mock.Mock(return_value=[0, 1])
        udp_replay.WAIT_TIME = 3
        udp_approx_vnf.get_nfvi_type = \
            mock.Mock(return_value="baremetal")

        udp_approx_vnf._vnf_process = mock.MagicMock()
        udp_approx_vnf._vnf_process.is_alive = \
            mock.Mock(return_value=1)
        udp_approx_vnf.setup_helper.setup_vnf_environment = mock.Mock()
        self.assertIsNone(udp_approx_vnf.instantiate(self.SCENARIO_CFG,
                                                        self.CONTEXT_CFG))

    @mock.patch(SSH_HELPER)
    def test_instantiate_panic(self, ssh, _):
        mock_ssh(ssh, exec_result=(1, "", ""))

        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'cgnapt': {'cfg': "",
                                                        'rules': ""}}
        udp_approx_vnf._run_udp_replay = mock.Mock(return_value=0)
        udp_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        udp_approx_vnf.deploy_udp_replay_vnf = mock.Mock(return_value=0)
        udp_approx_vnf.get_my_ports = mock.Mock(return_value=[0, 1])
        udp_replay.WAIT_TIME = 1
        udp_approx_vnf.get_nfvi_type = \
            mock.Mock(return_value="baremetal")
        udp_approx_vnf.setup_helper._validate_cpu_cfg = mock.Mock(return_value=[1, 2, 3])
        self.assertRaises(ValueError, udp_approx_vnf.instantiate,
                            self.SCENARIO_CFG, self.CONTEXT_CFG)

    def test_scale(self, _):
        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        flavor = ""
        self.assertRaises(NotImplementedError, udp_approx_vnf.scale, flavor)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, mock_time, _):
        mock_ssh(ssh)

        udp_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_approx_vnf._vnf_process = mock.MagicMock()
        udp_approx_vnf._vnf_process.terminate = mock.Mock()
        udp_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                       "01:01.1": "i40e"}
        udp_approx_vnf.execute_command = mock.Mock()
        udp_approx_vnf.dpdk_nic_bind = "dpdk_nic_bind.py"
        self.assertEqual(None, udp_approx_vnf.terminate())

if __name__ == '__main__':
    unittest.main()
