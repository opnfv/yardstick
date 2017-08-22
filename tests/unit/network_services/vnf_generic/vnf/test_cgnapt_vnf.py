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

import os
import unittest
import mock

from tests.unit import STL_MOCKS


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.cgnapt_vnf import CgnaptApproxVnf, \
        CgnaptApproxSetupEnvHelper
    from yardstick.network_services.vnf_generic.vnf import cgnapt_vnf
    from yardstick.network_services.nfvi.resource import ResourceProfile

TEST_FILE_YAML = 'nsb_test_case.yaml'


name = 'vnf__1'


class TestCgnaptApproxSetupEnvHelper(unittest.TestCase):

    def test__generate_ip_from_pool(self):

        ip = CgnaptApproxSetupEnvHelper._generate_ip_from_pool("1.2.3.4")
        self.assertEqual(next(ip), '1.2.3.4')
        self.assertEqual(next(ip), '1.2.4.4')
        self.assertEqual(next(ip), '1.2.5.4')

    def test__update_cgnat_script_file(self):

        sample = """\
# See the License for the specific language governing permissions and
# limitations under the License.

link 0 down
link 0 config {port0_local_ip} {port0_prefixlen}
link 0 up
link 1 down
link 1 config {port1_local_ip} {port1_prefixlen}
link 1 up
"""
        header = "This is a header"

        out = CgnaptApproxSetupEnvHelper._update_cgnat_script_file(header, sample.splitlines(), "")
        self.assertNotIn("This is a header", out)

    def test__get_cgnapt_confgi(self):

        c = CgnaptApproxSetupEnvHelper(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        c._get_ports_gateway = mock.Mock(return_value=3)
        ret = c._get_cgnapt_config([{"name": 'a'}, {}, {"name": "b"}, {}, {"name": "c"}])
        self.assertEqual(ret, [3, 3, 3])


@mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Process")
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

    scenario_cfg = {'options': {'packetsize': 64, 'traffic_type': 4,
                                'rfc2544': {'allowed_drop_rate': '0.8 - 1'},
                                'vnf__1': {'rules': 'acl_1rule.yaml',
                                           'vnf_config': {'lb_config': 'SW',
                                                          'lb_count': 1,
                                                          'worker_config':
                                                          '1C/1T',
                                                          'worker_threads': 1}}
                                },
                    'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
                    'task_path': '/tmp',
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

    def test___init__(self, mock_process):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
        self.assertIsNone(cgnapt_approx_vnf._vnf_process)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_collect_kpi(self, mock_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf.q_in = mock.MagicMock()
            cgnapt_approx_vnf.q_out = mock.MagicMock()
            cgnapt_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
            cgnapt_approx_vnf.resource = mock.Mock(autospec=ResourceProfile)
            result = {'packets_dropped': 0, 'packets_fwd': 0, 'packets_in': 0}
            self.assertEqual(result, cgnapt_approx_vnf.collect_kpi())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_vnf_execute_command(self, mock_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf.q_in = mock.MagicMock()
            cgnapt_approx_vnf.q_out = mock.MagicMock()
            cgnapt_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
            cmd = "quit"
            self.assertEqual("", cgnapt_approx_vnf.vnf_execute(cmd))

    def test_get_stats(self, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf.q_in = mock.MagicMock()
            cgnapt_approx_vnf.q_out = mock.MagicMock()
            cgnapt_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
            mock_result = \
                "CG-NAPT(.*\n)*Received 100, Missed 0, Dropped 0,Translated 100,ingress"
            cgnapt_approx_vnf.vnf_execute = mock.Mock(return_value=mock_result)
            self.assertListEqual(list(mock_result), list(cgnapt_approx_vnf.get_stats()))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.eval")
    @mock.patch('yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.open')
    def test_run_vcgnapt(self, hex, eval, mock_open, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf._build_config = mock.MagicMock()
            cgnapt_approx_vnf.queue_wrapper = mock.MagicMock()
            cgnapt_approx_vnf.ssh_helper = mock.MagicMock()
            cgnapt_approx_vnf.ssh_helper.run = mock.MagicMock()
            cgnapt_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
            cgnapt_approx_vnf._run()
            cgnapt_approx_vnf.ssh_helper.run.assert_called_once()

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    def test_instantiate(self, mock_context, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf.ssh_helper = ssh
            cgnapt_approx_vnf.deploy_helper = mock.MagicMock()
            cgnapt_approx_vnf.resource_helper = mock.MagicMock()
            cgnapt_approx_vnf._build_config = mock.MagicMock()
            self.scenario_cfg['vnf_options'] = {'acl': {'cfg': "",
                                                        'rules': ""}}
            cgnapt_approx_vnf.q_out.put("pipeline>")
            cgnapt_vnf.WAIT_TIME = 3
            self.scenario_cfg.update({"nodes": {"vnf__1": ""}})
            self.assertIsNone(cgnapt_approx_vnf.instantiate(self.scenario_cfg,
                                                            self.context_cfg))

    def test_scale(self, mock_process):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
        flavor = ""
        self.assertRaises(NotImplementedError, cgnapt_approx_vnf.scale, flavor)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_terminate(self, mock_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf._vnf_process = mock.MagicMock()
            cgnapt_approx_vnf._vnf_process.terminate = mock.Mock()
            cgnapt_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                              "01:01.1": "i40e"}
            cgnapt_approx_vnf.vnf_execute = mock.MagicMock()
            cgnapt_approx_vnf.ssh_helper = ssh_mock
            cgnapt_approx_vnf.dpdk_nic_bind = "dpdk_nic_bind.py"
            cgnapt_approx_vnf._resource_collect_stop = mock.Mock()
            self.assertEqual(None, cgnapt_approx_vnf.terminate())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.cgnapt_vnf.time")
    def test__vnf_up_post(self, mock_time, mock_cgnapt_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            cgnapt_approx_vnf = CgnaptApproxVnf(name, vnfd)
            cgnapt_approx_vnf._vnf_process = mock.MagicMock()
            cgnapt_approx_vnf._vnf_process.terminate = mock.Mock()
            cgnapt_approx_vnf.vnf_execute = mock.MagicMock()
            cgnapt_approx_vnf.ssh_helper = ssh_mock
            cgnapt_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
            cgnapt_approx_vnf._resource_collect_stop = mock.Mock()
            cgnapt_approx_vnf._vnf_up_post()
            cgnapt_approx_vnf.vnf_execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()
