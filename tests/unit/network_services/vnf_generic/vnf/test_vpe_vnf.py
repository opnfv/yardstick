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

from yardstick.network_services.vnf_generic.vnf.vpe_vnf import VpeApproxVnf
from yardstick.network_services.vnf_generic.vnf.vpe_vnf import ConfigCreate
from yardstick.network_services.vnf_generic.vnf import vpe_vnf
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.vnf_generic.vnf.base import \
    QueueFileWrapper

TEST_FILE_YAML = 'nsb_test_case.yaml'


class TestConfigCreate(unittest.TestCase):

    def test___init__(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertEqual(vpe_config_vnf.socket, 0)

    def test__get_firewall_script(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertIsNotNone(
            vpe_config_vnf.get_firewall_script("5", "11.1.1.1"))

    def test__get_flow_classification_script(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertIsNotNone(
            vpe_config_vnf.get_flow_classfication_script("5"))

    def test__get_flow_action(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertIsNotNone(
            vpe_config_vnf.get_flow_action("5"))

    def test__get_flow_action2(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertIsNotNone(
            vpe_config_vnf.get_flow_action2("5"))

    def test__get_route_script(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertIsNotNone(
            vpe_config_vnf.get_route_script(
                "5", "1.1.1.1", "00:00:00:00:00:02"))

    def test__get_route_script2(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        self.assertIsNotNone(
            vpe_config_vnf.get_route_script2(
                "5", "1.1.1.1", "00:00:00:00:00:02"))

    def test__generate_vpe_script(self):
        vpe_config_vnf = ConfigCreate([0], [0], 0)
        intf = [{"virtual-interface":
                {"dst_ip": "1.1.1.1", "dst_mac": "00:00:00:00:00:00:02"}}]
        self.assertIsNotNone(vpe_config_vnf.generate_vpe_script(intf))

    def test__create_vpe_config(self):
        vpe_config_vnf = ConfigCreate([0], [1], 0)
        curr_path = os.path.dirname(os.path.abspath(__file__))
        vpe_cfg = "samples/vnf_samples/nsut/vpe/vpe_config"
        vnf_cfg = \
            os.path.join(curr_path, "../../../../../%s" % vpe_cfg)
        result = vpe_config_vnf.create_vpe_config(vnf_cfg)
        os.system("git checkout -- %s" % vnf_cfg)
        self.assertIsNone(result)


class TestVpeApproxVnf(unittest.TestCase):
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
               'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'}]}}

    scenario_cfg = {'tc_options': {'rfc2544':
                                   {'allowed_drop_rate': '0.8 - 1'}},
                    'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
                    'tc': 'tc_ipv4_1Mflow_64B_packetsize',
                    'runner': {'object': 'NetworkServiceTestCase',
                               'interval': 35,
                               'output_filename': '/tmp/yardstick.out',
                               'runner_id': 74476, 'duration': 400,
                               'type': 'Duration'},
                    'traffic_profile': 'ipv4_throughput_vpe.yaml',
                    'traffic_options': {'flow': 'ipv4_Packets_vpe.yaml',
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
                              'VNF model': 'vpe_vnf.yaml'}}}

    def test___init__(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vpe_approx_vnf = VpeApproxVnf(vnfd)
        self.assertIsNone(vpe_approx_vnf._vnf_process)

    def test_collect_kpi(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            vpe_approx_vnf.resource = mock.Mock(autospec=ResourceProfile)
            vpe_approx_vnf.resource.check_if_sa_running = \
                mock.Mock(return_value=[0, 1])
            vpe_approx_vnf.resource.amqp_collect_nfvi_kpi= \
                mock.Mock(return_value={})
            result = {'pkt_in_down_stream': 0,
                      'pkt_in_up_stream': 0,
                      'collect_stats': {'core': {}},
                      'pkt_drop_down_stream': 0, 'pkt_drop_up_stream': 0}
            self.assertEqual(result, vpe_approx_vnf.collect_kpi())

    def test_execute_command(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            cmd = "quit"
            self.assertEqual("", vpe_approx_vnf.execute_command(cmd))

    def test_get_stats_vpe(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            vpe_approx_vnf.execute_command = \
                mock.Mock(return_value="Pkts in: 101\r\n\tPkts dropped by AH: 100\r\n\tPkts dropped by other: 100")
            result = {'pkt_in_down_stream': 202, 'pkt_in_up_stream': 202,
                      'pkt_drop_down_stream': 400, 'pkt_drop_up_stream': 400}
            self.assertEqual(result, vpe_approx_vnf.get_stats_vpe())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test_run_vpe(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            curr_path = os.path.dirname(os.path.abspath(__file__))
            vpe_vnf = os.path.join(curr_path, "vpe_config")
            queue_wrapper = \
                QueueFileWrapper(vpe_approx_vnf.q_in,
                                 vpe_approx_vnf.q_out, "pipeline>")
            vpe_approx_vnf.tc_file_name = \
                self._get_file_abspath(TEST_FILE_YAML)
            vpe_approx_vnf.generate_port_pairs = mock.Mock()
            vpe_approx_vnf.tg_port_pairs = [[[0], [1]]]
            vpe_approx_vnf.vnf_port_pairs = [[[0], [1]]]
            result = vpe_approx_vnf._run_vpe(queue_wrapper, vpe_vnf)
            os.system("git checkout -- %s" % vpe_vnf)
            self.assertEqual(None, result)

    def test_instantiate(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            self.scenario_cfg['vnf_options'] = {'vpe': {'cfg': ""}}
            vpe_approx_vnf._run_vpe = mock.Mock(return_value=0)
            vpe_approx_vnf._resource_collect_start = mock.Mock(return_value=0)
            vpe_approx_vnf.q_out.put("pipeline>")
            vpe_vnf.WAIT_TIME = 3
            vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
            self.assertEqual(0, vpe_approx_vnf.instantiate(self.scenario_cfg,
                             self.context_cfg))

    def test_instantiate_panic(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            self.scenario_cfg['vnf_options'] = {'vpe': {'cfg': ""}}
            vpe_approx_vnf._run_vpe = mock.Mock(return_value=0)
            vpe_vnf.WAIT_TIME = 1
            vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
            self.assertRaises(RuntimeError, vpe_approx_vnf.instantiate,
                              self.scenario_cfg, self.context_cfg)

    def test_get_nfvi_type(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vpe_approx_vnf = VpeApproxVnf(vnfd)
        self.scenario_cfg['tc'] = self._get_file_abspath("nsb_test_case")
        self.assertEqual("baremetal",
                         vpe_approx_vnf.get_nfvi_type(self.scenario_cfg))

    def test_scale(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vpe_approx_vnf = VpeApproxVnf(vnfd)
        flavor = ""
        self.assertRaises(NotImplementedError, vpe_approx_vnf.scale, flavor)

    def test_setup_vnf_environment(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vpe_approx_vnf = VpeApproxVnf(vnfd)
            self.assertEqual(None,
                             vpe_approx_vnf.setup_vnf_environment(ssh_mock))

    def test_terminate(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vpe_approx_vnf = VpeApproxVnf(vnfd)
        self.assertEqual(None, vpe_approx_vnf.terminate())

if __name__ == '__main__':
    unittest.main()
