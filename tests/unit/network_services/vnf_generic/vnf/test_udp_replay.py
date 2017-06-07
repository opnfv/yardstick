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

from yardstick.network_services.vnf_generic.vnf.udp_replay import \
    UdpReplayApproxVnf
from yardstick.network_services.vnf_generic.vnf import udp_replay
from yardstick.network_services.vnf_generic.vnf.base import \
    QueueFileWrapper

TEST_FILE_YAML = 'nsb_test_case.yaml'


class TestUdpReplayApproxVnf(unittest.TestCase):
    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
             [{'short-name': 'VpeVnf',
               'vdu':
               [{'routing_table':
                 [{'network': '152.16.100.20',
                   'netmask': '255.255.255.0',
                   'gateway': '152.16.100.20',
                   'if': 'xe0'},
                  {'network': '152.16.40.20',
                   'netmask': '255.255.255.0',
                   'gateway': '152.16.40.20',
                   'if': 'xe1'}],
                 'description': 'VPE approximation using DPDK',
                 'name': 'vpevnf-baremetal',
                 'nd_route_tbl':
                 [{'network': '0064:ff9b:0:0:0:0:9810:6414',
                   'netmask': '112',
                   'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                   'if': 'xe0'},
                  {'network': '0064:ff9b:0:0:0:0:9810:2814',
                   'netmask': '112',
                   'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                   'if': 'xe1'}],
                 'id': 'vpevnf-baremetal',
                 'external-interface':
                 [{'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:04',
                    'vpci': '0000:05:00.0',
                    'local_ip': '152.16.100.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '0',
                    'bandwidth': '10 Gbps',
                    'driver': "i40e",
                    'dst_ip': '152.16.100.20',
                    'local_iface_name': 'xe0',
                    'local_mac': '00:00:00:00:00:02'},
                   'vnfd-connection-point-ref': 'xe0',
                   'name': 'xe0'},
                  {'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:03',
                    'vpci': '0000:05:00.1',
                    'local_ip': '152.16.40.19',
                    'type': 'PCI-PASSTHROUGH',
                    'driver': "i40e",
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '1',
                    'bandwidth': '10 Gbps',
                    'dst_ip': '152.16.40.20',
                    'local_iface_name': 'xe1',
                    'local_mac': '00:00:00:00:00:01'},
                   'vnfd-connection-point-ref': 'xe1',
                   'name': 'xe1'}]}],
               'description': 'Vpe approximation using DPDK',
               'mgmt-interface':
                   {'vdu-id': 'vpevnf-baremetal',
                    'host': '1.2.1.1',
                    'password': 'r00t',
                    'user': 'root',
                    'ip': '1.2.1.1'},
               'benchmark':
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'UdpReplayApproxVnf', 'name': 'VPEVnfSsh'}]}}

    scenario_cfg = {'options': {'packetsize': 64, 'traffic_type': 4 ,
                                'rfc2544': {'allowed_drop_rate': '0.8 - 1'},
                                'vnf__1': {'rules': 'acl_1rule.yaml',
                                           'vnf_config': {'lb_config': 'SW',
                                                          'lb_count': 1,
                                                          'worker_config':
                                                          '1C/1T',
                                                          'worker_threads': 1}}
                               },
                    'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
                    'tc': 'tc_ipv4_1Mflow_64B_packetsize',
                    'runner': {'object': 'NetworkServiceTestCase',
                               'interval': 35,
                               'output_filename': '/tmp/yardstick.out',
                               'runner_id': 74476, 'duration': 400,
                               'type': 'Duration'},
                    'traffic_profile': 'ipv4_throughput_acl.yaml',
                    'traffic_options': {'flow': 'ipv4_Packets_acl.yaml',
                                        'imix': 'imix_voice.yaml'},
                    'type': 'ISB',
                    'nodes': {'tg__2': 'trafficgen_2.yardstick',
                              'tg__1': 'trafficgen_1.yardstick',
                              'vnf__1': 'vnf.yardstick'},
                    'topology': 'vpe-tg-topology-baremetal.yaml'}

    context_cfg = {'nodes': {'tg__2':
                             {'member-vnf-index': '3',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_2.yardstick',
                              'vnfd-id-ref': 'tg__2',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens513f0',
                                       'vld_id': 'public',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.20',
                                       'dst_mac': '00:00:00:00:00:01',
                                       'local_mac': '00:00:00:00:00:03',
                                       'dst_ip': '152.16.40.19',
                                       'driver': 'ixgbe',
                                       'vpci': '0000:02:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens513f1',
                                       'netmask': '255.255.255.0',
                                       'network': '202.16.100.0',
                                       'local_ip': '202.16.100.20',
                                       'local_mac': '00:1e:67:d0:60:5d',
                                       'driver': 'ixgbe',
                                       'vpci': '0000:02:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'l3fwd_vnf.yaml',
                              'user': 'root'},
                             'tg__1':
                             {'member-vnf-index': '1',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_1.yardstick',
                              'vnfd-id-ref': 'tg__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens785f0',
                                       'vld_id': 'private',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.20',
                                       'dst_mac': '00:00:00:00:00:02',
                                       'local_mac': '00:00:00:00:00:04',
                                       'dst_ip': '152.16.100.19',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens785f1',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.21',
                                       'local_mac': '00:00:00:00:00:01',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'tg_rfc2544_tpl.yaml',
                              'user': 'root'},
                             'vnf__1':
                             {'name': 'vnf.yardstick',
                              'vnfd-id-ref': 'vnf__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens786f0',
                                       'vld_id': 'private',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.19',
                                       'dst_mac': '00:00:00:00:00:04',
                                       'local_mac': '00:00:00:00:00:02',
                                       'dst_ip': '152.16.100.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens786f1',
                                       'vld_id': 'public',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.19',
                                       'dst_mac': '00:00:00:00:00:03',
                                       'local_mac': '00:00:00:00:00:01',
                                       'dst_ip': '152.16.40.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'routing_table':
                              [{'netmask': '255.255.255.0',
                                'gateway': '152.16.100.20',
                                'network': '152.16.100.20',
                                'if': 'xe0'},
                               {'netmask': '255.255.255.0',
                                'gateway': '152.16.40.20',
                                'network': '152.16.40.20',
                                'if': 'xe1'}],
                              'member-vnf-index': '2',
                              'host': '1.2.1.1',
                              'role': 'vnf',
                              'user': 'root',
                              'nd_route_tbl':
                              [{'netmask': '112',
                                'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                                'network': '0064:ff9b:0:0:0:0:9810:6414',
                                'if': 'xe0'},
                               {'netmask': '112',
                                'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                                'network': '0064:ff9b:0:0:0:0:9810:2814',
                                'if': 'xe1'}],
                              'password': 'r00t',
                              'VNF model': 'udp_replay.yaml'}}}

    def test___init__(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        udp_approx_vnf = UdpReplayApproxVnf(vnfd)
        self.assertIsNone(udp_approx_vnf._vnf_process)

    def test_collect_kpi(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            result = "stats\r\r\n\r\nUDP_Replay stats:\r\n--------------\r\n" \
            "Port\t\tRx Packet\t\tTx Packet\t\tRx Pkt Drop\t\tTx Pkt Drop \r\n"\
            "0\t\t7374156\t\t7374136\t\t\t0\t\t\t0\r\n" \
            "1\t\t7374316\t\t7374315\t\t\t0\t\t\t0\r\n\r\nReplay>\r\r\nReplay>"
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            udp_approx_vnf.my_ports = [0, 1]
            udp_approx_vnf.interfaces = vnfd["vdu"][0]['external-interface']
            udp_approx_vnf.get_stats_udp_replay = \
                mock.Mock(return_value=result)
            result = {'collect_stats': {}, 'packets_dropped': 0,
                      'packets_fwd': 14748451, 'packets_in': 14748472}
            self.assertEqual(result, udp_approx_vnf.collect_kpi())

    def test_execute_command(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            cmd = "quit"
            self.assertEqual("", udp_approx_vnf.execute_command(cmd))

    def test_get_stats_udp_replay(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            mock_result = \
                "CG-NAPT(.*\n)*Received 100, Missed 0, Dropped 0,Translated 100,ingress"
            udp_approx_vnf.execute_command = \
                mock.Mock(return_value=mock_result)
            self.assertEqual(mock_result,
                             udp_approx_vnf.get_stats_udp_replay())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.udp_replay.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.udp_replay.eval")
    def test_run_udp_replay(self, hex, eval):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            curr_path = os.path.dirname(os.path.abspath(__file__))
            udp_approx_vnf.vnf_cfg = os.path.join(curr_path, "vpe_config")
            queue_wrapper = \
                QueueFileWrapper(udp_approx_vnf.q_in,
                                 udp_approx_vnf.q_out, "pipeline>")
            udp_approx_vnf.tc_file_name = \
                self._get_file_abspath(TEST_FILE_YAML)
            udp_approx_vnf.generate_port_pairs = mock.Mock()
            udp_approx_vnf.tg_port_pairs = [[[0], [1]]]
            udp_approx_vnf.vnf_port_pairs = [[[0], [1]]]
            udp_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                      'lb_count': 1,
                                      'worker_config': '1C/1T',
                                      'worker_threads': 1}
            udp_approx_vnf.options = {'traffic_type': '4',
                                      'topology': 'nsb_test_case.yaml'}
            udp_approx_vnf.topology = "nsb_test_case.yaml"
            udp_approx_vnf.nfvi_type = "baremetal"
            udp_approx_vnf._provide_config_file = mock.Mock()
            udp_approx_vnf.my_ports = [0, 1]
            udp_approx_vnf.interfaces = vnfd["vdu"][0]['external-interface']

            self.assertEqual(None,
                             udp_approx_vnf._run_udp_replay(queue_wrapper))

    def test_deploy_udp_replay_vnf(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            udp_approx_vnf.deploy = mock.MagicMock()
            udp_approx_vnf.deploy.deploy_vnfs = mock.Mock()
            udp_approx_vnf.connection = ssh_mock
            udp_approx_vnf.bin_path = "/tmp"
            self.assertEqual(None, udp_approx_vnf.deploy_udp_replay_vnf())

    def test_get_my_ports(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            udp_approx_vnf.deploy = mock.MagicMock()
            udp_approx_vnf.deploy.deploy_vnfs = mock.Mock()
            udp_approx_vnf.connection = ssh_mock
            udp_approx_vnf.bin_path = "/tmp"
            udp_approx_vnf.topology = 'dummy'
            udp_approx_vnf.generate_port_pairs = mock.Mock(return_value=[[[0]],
                                                                         [[1]]])
            udp_approx_vnf.tg_port_pairs = [[[0], [1]]]
            self.assertEqual([0, 1], udp_approx_vnf.get_my_ports())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.udp_replay.Context")
    def test_instantiate(self, Context):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            self.scenario_cfg['vnf_options'] = {'cgnapt': {'cfg': "",
                                                'rules': ""}}
            udp_approx_vnf._run_udp_replay = mock.Mock(return_value=0)
            udp_approx_vnf._parse_rule_file = mock.Mock(return_value={})
            udp_approx_vnf.deploy_udp_replay_vnf = mock.Mock(return_value=1)
            udp_approx_vnf.q_out.put("Replay>")
            udp_approx_vnf.get_my_ports = mock.Mock(return_value=[0, 1])
            udp_replay.WAIT_TIME = 3
            udp_approx_vnf.get_nfvi_type = \
                mock.Mock(return_value="baremetal")
            
            udp_approx_vnf._vnf_process = mock.MagicMock()
            udp_approx_vnf._vnf_process.is_alive = \
                mock.Mock(return_value=1)
            self.assertIsNone(udp_approx_vnf.instantiate("vnf__1", self.scenario_cfg,
                              self.context_cfg))

    @mock.patch("yardstick.network_services.vnf_generic.vnf.udp_replay.Context")
    def test_instantiate_panic(self, Context):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            self.scenario_cfg['vnf_options'] = {'cgnapt': {'cfg': "",
                                                'rules': ""}}
            udp_approx_vnf._run_udp_replay = mock.Mock(return_value=0)
            udp_approx_vnf._parse_rule_file = mock.Mock(return_value={})
            udp_approx_vnf.deploy_udp_replay_vnf = mock.Mock(return_value=0)
            udp_approx_vnf.get_my_ports = mock.Mock(return_value=[0, 1])
            udp_replay.WAIT_TIME = 1
            udp_approx_vnf.get_nfvi_type = \
                mock.Mock(return_value="baremetal")
            udp_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2 , 3])
            self.assertRaises(RuntimeError, udp_approx_vnf.instantiate,
                              "vnf__1", self.scenario_cfg, self.context_cfg)

    def test_get_nfvi_type(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        udp_approx_vnf = UdpReplayApproxVnf(vnfd)
        self.scenario_cfg['tc'] = self._get_file_abspath("nsb_test_case")
        udp_approx_vnf.nfvi_context = {}
        self.assertEqual("baremetal",
                         udp_approx_vnf.get_nfvi_type(self.scenario_cfg))

    def test_scale(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        udp_approx_vnf = UdpReplayApproxVnf(vnfd)
        flavor = ""
        self.assertRaises(NotImplementedError, udp_approx_vnf.scale, flavor)

    def test_setup_vnf_environment(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            self.assertEqual(None,
                             udp_approx_vnf.setup_vnf_environment(ssh_mock))

    def test_terminate(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            udp_approx_vnf = UdpReplayApproxVnf(vnfd)
            udp_approx_vnf._vnf_process = mock.MagicMock()
            udp_approx_vnf._vnf_process.terminate = mock.Mock()
            udp_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                           "01:01.1": "i40e"}
            udp_approx_vnf.execute_command = mock.Mock()
            udp_approx_vnf.connection = ssh_mock
            udp_approx_vnf.dpdk_nic_bind = "dpdk_nic_bind.py"
            self.assertEqual(None, udp_approx_vnf.terminate())

if __name__ == '__main__':
    unittest.main()
