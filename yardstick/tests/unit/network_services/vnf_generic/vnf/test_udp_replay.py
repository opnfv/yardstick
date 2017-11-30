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
import os

from tests.unit import STL_MOCKS
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh


SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.udp_replay import UdpReplayApproxVnf
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper


TEST_FILE_YAML = 'nsb_test_case.yaml'


NAME = "vnf__1"


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
                            'dpdk_port_num': 0,
                            'netmask': '255.255.255.0',
                            'dst_ip': '152.16.100.20',
                            'type': 'PCI-PASSTHROUGH',
                            'vld_id': 'uplink_0',
                            'ifname': 'xe0',
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
                            'dpdk_port_num': 1,
                            'netmask': '255.255.255.0',
                            'dst_ip': '152.16.40.20',
                            'type': 'PCI-PASSTHROUGH',
                            'vld_id': 'downlink_0',
                            'ifname': 'xe1',
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
                },
                "hw_csum": "false",
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
                        "vld_id": UdpReplayApproxVnf.UPLINK,
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
                        "vld_id": UdpReplayApproxVnf.DOWNLINK,
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
                        "vld_id": UdpReplayApproxVnf.DOWNLINK,
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
                        "vld_id": UdpReplayApproxVnf.UPLINK,
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

    def test___init__(self, *args):
        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        self.assertIsNone(udp_replay_approx_vnf._vnf_process)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD_0
        get_stats_ret_val = \
            "stats\r\r\n\r\nUDP_Replay stats:\r\n--------------\r\n" \
            "Port\t\tRx Packet\t\tTx Packet\t\tRx Pkt Drop\t\tTx Pkt Drop \r\n"\
            "0\t\t7374156\t\t7374136\t\t\t0\t\t\t0\r\n" \
            "1\t\t7374316\t\t7374315\t\t\t0\t\t\t0\r\n\r\nReplay>\r\r\nReplay>"
        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, vnfd)
        udp_replay_approx_vnf.q_in = mock.MagicMock()
        udp_replay_approx_vnf.q_out = mock.MagicMock()
        udp_replay_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        udp_replay_approx_vnf.all_ports = ["xe0", "xe1"]
        udp_replay_approx_vnf.get_stats = mock.Mock(return_value=get_stats_ret_val)

        result = {'collect_stats': {}, 'packets_dropped': 0,
                  'packets_fwd': 14748451, 'packets_in': 14748472}
        self.assertEqual(result, udp_replay_approx_vnf.collect_kpi())

    @mock.patch(SSH_HELPER)
    def test_get_stats(self, ssh, *args):
        mock_ssh(ssh)

        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_replay_approx_vnf.q_in = mock.MagicMock()
        udp_replay_approx_vnf.q_out = mock.MagicMock()
        udp_replay_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        mock_result = \
            "CG-NAPT(.*\n)*Received 100, Missed 0, Dropped 0,Translated 100,ingress"

        udp_replay_approx_vnf.vnf_execute = mock.Mock(return_value=mock_result)

        self.assertEqual(mock_result,
                         udp_replay_approx_vnf.get_stats())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test__build_config(self, ssh, mock_context, *args):
        mock_ssh(ssh)

        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_replay_approx_vnf.queue_wrapper = mock.MagicMock()
        udp_replay_approx_vnf.nfvi_context = mock_context
        udp_replay_approx_vnf.nfvi_context.attrs = {'nfvi_type': 'baremetal'}
        udp_replay_approx_vnf.setup_helper.bound_pci = []
        udp_replay_approx_vnf.ssh_helper.provision_tool = mock.MagicMock(return_value="tool_path")
        udp_replay_approx_vnf.scenario_helper = ScenarioHelper(name='vnf__1')
        udp_replay_approx_vnf.scenario_helper.scenario_cfg = self.SCENARIO_CFG

        cmd_line = udp_replay_approx_vnf._build_config()

        expected = \
            "sudo tool_path --log-level=5 -c 0x7 -n 4 -w  --  -p 0x3 --config='(0,0,1),(1,0,2)'"
        self.assertEqual(cmd_line, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.udp_replay.open')
    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test__build_pipeline_kwargs(self, ssh, mock_context, *args):
        mock_ssh(ssh)
        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_replay_approx_vnf.nfvi_context = mock_context
        udp_replay_approx_vnf.nfvi_context.attrs = {'nfvi_type': 'baremetal'}
        udp_replay_approx_vnf.setup_helper.bound_pci = ['0000:00:0.1', '0000:00:0.3']
        udp_replay_approx_vnf.all_ports = ["xe0", "xe1"]
        udp_replay_approx_vnf.ssh_helper.provision_tool = mock.MagicMock(return_value="tool_path")
        udp_replay_approx_vnf.scenario_helper = ScenarioHelper(name='vnf__1')
        udp_replay_approx_vnf.scenario_helper.scenario_cfg = self.SCENARIO_CFG

        udp_replay_approx_vnf._build_pipeline_kwargs()

        self.assertEqual(udp_replay_approx_vnf.pipeline_kwargs, {
            'config': '(0,0,1),(1,0,2)',
            'cpu_mask_hex': '0x7',
            'hw_csum': '',
            'port_mask_hex': '0x3',
            'tool_path': 'tool_path',
            'whitelist': '0000:00:0.1 -w 0000:00:0.3'
        })

    @mock.patch(SSH_HELPER)
    def test_run_udp_replay(self, ssh, *args):
        mock_ssh(ssh)

        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_replay_approx_vnf._build_config = mock.MagicMock()
        udp_replay_approx_vnf.queue_wrapper = mock.MagicMock()
        udp_replay_approx_vnf.scenario_helper = mock.MagicMock()

        udp_replay_approx_vnf._run()

        udp_replay_approx_vnf.ssh_helper.run.assert_called_once()

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, *args):
        mock_ssh(ssh)

        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_replay_approx_vnf.q_out.put("Replay>")
        udp_replay_approx_vnf.WAIT_TIME = 0
        udp_replay_approx_vnf.setup_helper.setup_vnf_environment = mock.Mock()

        udp_replay_approx_vnf.deploy_helper = mock.MagicMock()
        udp_replay_approx_vnf.deploy_vnfs = mock.MagicMock()
        self.assertIsNone(udp_replay_approx_vnf.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG))

        udp_replay_approx_vnf._vnf_process.is_alive = mock.Mock(return_value=1)
        udp_replay_approx_vnf._vnf_process.exitcode = 0

        self.assertEqual(udp_replay_approx_vnf.wait_for_instantiate(), 0)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch('yardstick.ssh.SSH')
    @mock.patch(SSH_HELPER)
    def test_instantiate_panic(self, *args):
        udp_replay_approx_vnf = UdpReplayApproxVnf(NAME, self.VNFD_0)
        udp_replay_approx_vnf.WAIT_TIME = 0
        udp_replay_approx_vnf.q_out.put("some text PANIC some text")
        udp_replay_approx_vnf.setup_helper.setup_vnf_environment = mock.Mock()

        udp_replay_approx_vnf.deploy_helper = mock.MagicMock()
        self.assertIsNone(udp_replay_approx_vnf.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG))
        with self.assertRaises(RuntimeError):
            udp_replay_approx_vnf.wait_for_instantiate()
