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

from yardstick.network_services.vnf_generic.vnf.cgnapt_vnf import CgnaptApproxVnf
from yardstick.network_services.vnf_generic.vnf import cgnapt_vnf
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.vnf_generic.vnf.base import \
    QueueFileWrapper

TEST_FILE_YAML = 'nsb_test_case.yaml'


class TestCgnaptApproxVnf(unittest.TestCase):
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
               'id': 'CgnaptApproxVnf', 'name': 'VPEVnfSsh'}]}}

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
                              'VNF model': 'cgnapt_vnf.yaml'}}}

    def test___init__(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        self.assertIsNone(cgnapt_approx_vnf._vnf_process)

    def test_collect_kpi(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            cgnapt_approx_vnf.resource = mock.Mock(autospec=ResourceProfile)
            cgnapt_approx_vnf.resource.check_if_sa_running = \
                mock.Mock(return_value=[0, 1])
            cgnapt_approx_vnf.resource.amqp_collect_nfvi_kpi = \
                mock.Mock(return_value={})
            result = {'collect_stats': {'core': {}}, 'packets_dropped': 0,
                      'packets_fwd': 0, 'packets_in': 0}
            self.assertEqual(result, cgnapt_approx_vnf.collect_kpi())

    def test_execute_command(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            cmd = "quit"
            self.assertEqual("", cgnapt_approx_vnf.execute_command(cmd))

    def test_add_static_cgnat(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        cgnapt_approx_vnf.execute_command = mock.Mock()
        interfaces = vnfd["vdu"][0]['external-interface']
        cgnapt_approx_vnf._get_cgnapt_config = mock.Mock(return_value=['4.4.4.4'])
        cgnapt_approx_vnf._get_random_public_pool_ip = mock.Mock(return_value='4.4.4.4')
        cgnapt_approx_vnf.execute_command = mock.Mock()
        cgnapt_approx_vnf.vnf_cfg = {'lb_config': 'HW', 'worker_threads': 1}
        cgnapt_approx_vnf.node_name = 'vnf__1'
        cgnapt_approx_vnf.options = {'vnf__1': {'napt': 'static'},
                                     'traffic_type': '4',
                                     'topology': 'nsb_test_case.yaml'}
        self.assertEqual(None,
                         cgnapt_approx_vnf._add_static_cgnat(['xe0', 'xe1'],
                                                             interfaces))

    def test__resource_collect_start(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        cgnapt_approx_vnf.execute_command = mock.Mock()
        cgnapt_approx_vnf.resource = mock.MagicMock()
        cgnapt_approx_vnf.resource.initiate_systemagent = mock.Mock()
        cgnapt_approx_vnf.resource.start = mock.Mock()
        cgnapt_approx_vnf.resource.amqp_process_for_nfvi_kpi = mock.Mock()
        self.assertEqual(None, cgnapt_approx_vnf._resource_collect_start())

    def test__resource_collect_stop(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        cgnapt_approx_vnf.execute_command = mock.Mock()
        cgnapt_approx_vnf.resource = mock.MagicMock()
        cgnapt_approx_vnf.resource.stop = mock.Mock()
        self.assertEqual(None, cgnapt_approx_vnf._resource_collect_stop())

    def test__collect_resource_kpi(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        cgnapt_approx_vnf.execute_command = mock.Mock()
        cgnapt_approx_vnf.resource = mock.MagicMock()
        cgnapt_approx_vnf.resource.check_if_sa_running = \
            mock.Mock(return_value=[1])
        cgnapt_approx_vnf.resource.amqp_collect_nfvi_kpi = \
            mock.Mock(return_value={})
        self.assertEqual({"core": {}},
                         cgnapt_approx_vnf._collect_resource_kpi())


    def test_get_stats_vcgnapt(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            mock_result = \
                "CG-NAPT(.*\n)*Received 100, Missed 0, Dropped 0,Translated 100,ingress"
            cgnapt_approx_vnf.execute_command = \
                mock.Mock(return_value=mock_result)
            self.assertEqual(mock_result,
                             cgnapt_approx_vnf.get_stats_vcgnapt())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.MultiPortConfig")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.eval")
    def test_run_vcgnapt(self, MultiPortConfig, hex, eval):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            curr_path = os.path.dirname(os.path.abspath(__file__))
            cgnapt_approx_vnf.vnf_cfg = os.path.join(curr_path, "vpe_config")
            queue_wrapper = \
                QueueFileWrapper(cgnapt_approx_vnf.q_in,
                                 cgnapt_approx_vnf.q_out, "pipeline>")
            cgnapt_approx_vnf.tc_file_name = \
                self._get_file_abspath(TEST_FILE_YAML)
            cgnapt_approx_vnf.generate_port_pairs = mock.Mock()
            cgnapt_approx_vnf.tg_port_pairs = [[[0], [1]]]
            cgnapt_approx_vnf.vnf_port_pairs = [[[0], [1]]]
            cgnapt_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                      'lb_count': 1,
                                      'worker_config': '1C/1T',
                                      'worker_threads': 1}
            cgnapt_approx_vnf.options = {'traffic_type': '4',
                                      'topology': 'nsb_test_case.yaml'}
            cgnapt_approx_vnf.topology = "nsb_test_case.yaml"
            cgnapt_approx_vnf.nfvi_type = "baremetal"
            cgnapt_approx_vnf._provide_config_file = mock.Mock()

            self.assertEqual(None,
                             cgnapt_approx_vnf._run_vcgnapt(queue_wrapper))

    def test_deploy_cgnapt_vnf(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            cgnapt_approx_vnf.deploy = mock.MagicMock()
            cgnapt_approx_vnf.deploy.deploy_vnfs = mock.Mock()
            cgnapt_approx_vnf.connection = ssh_mock
            cgnapt_approx_vnf.bin_path = "/tmp"
            self.assertEqual(None, cgnapt_approx_vnf.deploy_cgnapt_vnf())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.Context")
    def test_instantiate(self, Context):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            self.scenario_cfg['vnf_options'] = {'cgnapt': {'cfg': "",
                                                'rules': ""}}
            cgnapt_approx_vnf._run_vcgnapt = mock.Mock(return_value=0)
            cgnapt_approx_vnf._parse_rule_file = mock.Mock(return_value={})
            cgnapt_approx_vnf._resource_collect_start = \
                mock.Mock(return_value=0)
            cgnapt_approx_vnf.deploy_cgnapt_vnf = mock.Mock(return_value=0)
            cgnapt_approx_vnf.q_out.put("pipeline>")
            cgnapt_vnf.WAIT_TIME = 3
            cgnapt_approx_vnf.get_nfvi_type = \
                mock.Mock(return_value="baremetal")
            cgnapt_approx_vnf._vnf_process = mock.MagicMock()
            cgnapt_approx_vnf._vnf_process.is_alive = mock.Mock(return_value=1)
            cgnapt_approx_vnf._vnf_process.exitcode.return_value = 0
            cgnapt_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2 , 3])
            self.assertEqual(0, cgnapt_approx_vnf.instantiate("vnf__1", self.scenario_cfg,
                              self.context_cfg))

    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.Context")
    def test_instantiate_panic(self, Context):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            self.scenario_cfg['vnf_options'] = {'cgnapt': {'cfg': "",
                                                'rules': ""}}
            cgnapt_approx_vnf._run_vcgnapt = mock.Mock(return_value=0)
            cgnapt_approx_vnf._parse_rule_file = mock.Mock(return_value={})
            cgnapt_approx_vnf.deploy_cgnapt_vnf = mock.Mock(return_value=0)
            cgnapt_vnf.WAIT_TIME = 1
            cgnapt_approx_vnf.get_nfvi_type = \
                mock.Mock(return_value="baremetal")
            cgnapt_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2 , 3])
            self.assertRaises(RuntimeError, cgnapt_approx_vnf.instantiate,
                              "vnf__1", self.scenario_cfg, self.context_cfg)

    def test_get_nfvi_type(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        self.scenario_cfg['tc'] = self._get_file_abspath("nsb_test_case")
        cgnapt_approx_vnf.nfvi_context = {}
        self.assertEqual("baremetal",
                         cgnapt_approx_vnf.get_nfvi_type(self.scenario_cfg))

    def test_scale(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
        flavor = ""
        self.assertRaises(NotImplementedError, cgnapt_approx_vnf.scale, flavor)

    def test_setup_vnf_environment(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            self.assertEqual(None,
                             cgnapt_approx_vnf.setup_vnf_environment(ssh_mock))

    def test_terminate(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(vnfd)
            cgnapt_approx_vnf._vnf_process = mock.MagicMock()
            cgnapt_approx_vnf._vnf_process.terminate = mock.Mock()
            cgnapt_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                           "01:01.1": "i40e"}
            cgnapt_approx_vnf.execute_command = mock.Mock()
            cgnapt_approx_vnf.connection = ssh_mock
            cgnapt_approx_vnf.dpdk_nic_bind = "dpdk_nic_bind.py"
            cgnapt_approx_vnf._resource_collect_stop = mock.Mock()
            self.assertEqual(None, cgnapt_approx_vnf.terminate())

if __name__ == '__main__':
    unittest.main()
