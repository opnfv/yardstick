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

from yardstick.tests import STL_MOCKS
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh
from yardstick.common import utils


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.acl_vnf import AclApproxVnf
    from yardstick.network_services.nfvi.resource import ResourceProfile


TEST_FILE_YAML = 'nsb_test_case.yaml'
SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'


name = 'vnf__1'


@mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Process")
class TestAclApproxVnf(unittest.TestCase):
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
                    'dpdk_port_num': 0,
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
                    'dpdk_port_num': 1,
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
               'id': 'AclApproxVnf', 'name': 'VPEVnfSsh'}]}}

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
                                       'vld_id': AclApproxVnf.DOWNLINK,
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
                                       'vld_id': AclApproxVnf.UPLINK,
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
                                       'vld_id': AclApproxVnf.UPLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.19',
                                       'dst_mac': '00:00:00:00:00:04',
                                       'local_mac': '00:00:00:00:00:02',
                                       'dst_ip': '152.16.100.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens786f1',
                                       'vld_id': AclApproxVnf.DOWNLINK,
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
                              'VNF model': 'acl_vnf.yaml'}}}

    def test___init__(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        self.assertIsNone(acl_approx_vnf._vnf_process)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        acl_approx_vnf.q_in = mock.MagicMock()
        acl_approx_vnf.q_out = mock.MagicMock()
        acl_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        acl_approx_vnf.resource = mock.Mock(autospec=ResourceProfile)
        acl_approx_vnf.vnf_execute = mock.Mock(return_value="")
        result = {'packets_dropped': 0, 'packets_fwd': 0, 'packets_in': 0}
        self.assertEqual(result, acl_approx_vnf.collect_kpi())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_vnf_execute_command(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        acl_approx_vnf.q_in = mock.MagicMock()
        acl_approx_vnf.q_out = mock.MagicMock()
        acl_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        cmd = "quit"
        self.assertEqual("", acl_approx_vnf.vnf_execute(cmd))

    @mock.patch(SSH_HELPER)
    def test_get_stats(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        acl_approx_vnf.q_in = mock.MagicMock()
        acl_approx_vnf.q_out = mock.MagicMock()
        acl_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        result = "ACL TOTAL: pkts_processed: 100, pkts_drop: 0, spkts_received: 100"
        acl_approx_vnf.vnf_execute = mock.Mock(return_value=result)
        self.assertEqual(result, acl_approx_vnf.get_stats())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.acl_vnf.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.acl_vnf.eval")
    @mock.patch('yardstick.network_services.vnf_generic.vnf.acl_vnf.open')
    @mock.patch(SSH_HELPER)
    def test_run_acl(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        acl_approx_vnf._build_config = mock.MagicMock()
        acl_approx_vnf.queue_wrapper = mock.MagicMock()
        acl_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
        acl_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                  'lb_count': 1,
                                  'worker_config': '1C/1T',
                                  'worker_threads': 1}
        acl_approx_vnf.all_options = {'traffic_type': '4',
                                      'topology': 'nsb_test_case.yaml'}
        acl_approx_vnf._run()
        acl_approx_vnf.ssh_helper.run.assert_called_once()

    @mock.patch("yardstick.network_services.vnf_generic.vnf.acl_vnf.YangModel")
    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        acl_approx_vnf.deploy_helper = mock.MagicMock()
        acl_approx_vnf.resource_helper = mock.MagicMock()
        acl_approx_vnf._build_config = mock.MagicMock()
        self.scenario_cfg['vnf_options'] = {'acl': {'cfg': "",
                                                    'rules': ""}}
        acl_approx_vnf.q_out.put("pipeline>")
        acl_approx_vnf.WAIT_TIME = 0
        self.scenario_cfg.update({"nodes": {"vnf__1": ""}})
        self.assertIsNone(acl_approx_vnf.instantiate(self.scenario_cfg,
                                                     self.context_cfg))

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        acl_approx_vnf = AclApproxVnf(name, vnfd)
        acl_approx_vnf._vnf_process = mock.MagicMock()
        acl_approx_vnf._vnf_process.terminate = mock.Mock()
        acl_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                       "01:01.1": "i40e"}
        acl_approx_vnf.vnf_execute = mock.MagicMock()
        acl_approx_vnf.dpdk_devbind = "dpdk-devbind.py"
        acl_approx_vnf._resource_collect_stop = mock.Mock()
        self.assertIsNone(acl_approx_vnf.terminate())
