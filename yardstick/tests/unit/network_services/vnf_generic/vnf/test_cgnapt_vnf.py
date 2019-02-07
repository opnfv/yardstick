# Copyright (c) 2016-2019 Intel Corporation
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

from copy import deepcopy
import time

import mock
import unittest

from yardstick.benchmark.contexts import base as ctx_base
from yardstick.common import utils
from yardstick.common import process
from yardstick.network_services.vnf_generic.vnf import cgnapt_vnf
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.nfvi import resource


TEST_FILE_YAML = 'nsb_test_case.yaml'
name = 'vnf__0'


class TestCgnaptApproxSetupEnvHelper(unittest.TestCase):

    def test__generate_ip_from_pool(self):

        _ip = '1.2.3.4'
        ip = cgnapt_vnf.CgnaptApproxSetupEnvHelper._generate_ip_from_pool(_ip)
        self.assertEqual(next(ip), _ip)
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

        out = cgnapt_vnf.CgnaptApproxSetupEnvHelper._update_cgnat_script_file(
            header, sample.splitlines())
        self.assertNotIn("This is a header", out)

    def test__get_cgnapt_config(self):
        vnfd_helper = mock.MagicMock()
        vnfd_helper.port_pairs.uplink_ports = [{"name": 'a'}, {"name": "b"}, {"name": "c"}]

        helper = cgnapt_vnf.CgnaptApproxSetupEnvHelper(
            vnfd_helper, mock.Mock(), mock.Mock())
        result = helper._get_cgnapt_config()
        self.assertIsNotNone(result)

    def test_scale(self):
        helper = cgnapt_vnf.CgnaptApproxSetupEnvHelper(
            mock.Mock(), mock.Mock(), mock.Mock())
        with self.assertRaises(NotImplementedError):
            helper.scale()

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.open')
    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.MultiPortConfig')
    @mock.patch.object(utils, 'open_relative_file')
    def test_build_config(self, *args):
        vnfd_helper = mock.Mock()
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.vnf_cfg = {'lb_config': 'HW'}
        scenario_helper.options = {}
        scenario_helper.all_options = {}

        cgnat_approx_setup_helper = cgnapt_vnf.CgnaptApproxSetupEnvHelper(
            vnfd_helper, ssh_helper, scenario_helper)

        cgnat_approx_setup_helper.ssh_helper.provision_tool = mock.Mock(return_value='tool_path')
        cgnat_approx_setup_helper.ssh_helper.all_ports = mock.Mock()
        cgnat_approx_setup_helper.vnfd_helper.port_nums = mock.Mock(return_value=[0, 1])
        expected = 'sudo tool_path -p 0x3 -f /tmp/cgnapt_config -s /tmp/cgnapt_script  --hwlb 3'
        self.assertEqual(cgnat_approx_setup_helper.build_config(), expected)


@mock.patch.object(sample_vnf, 'Process')
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
               'id': 'CgnaptApproxVnf', 'name': 'VPEVnfSsh'}]}}

    SCENARIO_CFG = {
        'options': {
            'packetsize': 64,
            'traffic_type': 4,
            'rfc2544': {
                'allowed_drop_rate': '0.8 - 1',
            },
            'vnf__0': {
                'napt': 'dynamic',
                'vnf_config': {
                    'lb_config': 'SW',
                    'lb_count': 1,
                    'worker_config':
                    '1C/1T',
                    'worker_threads': 1,
                },
            },
            'flow': {'count': 1,
                     'dst_ip': [{'tg__1': 'xe0'}],
                     'public_ip': [''],
                     'src_ip': [{'tg__0': 'xe0'}]},
        },
        'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
        'task_path': '/tmp',
        'tc': 'tc_ipv4_1Mflow_64B_packetsize',
        'runner': {
            'object': 'NetworkServiceTestCase',
            'interval': 35,
            'output_filename': '/tmp/yardstick.out',
            'runner_id': 74476,
            'duration': 400,
            'type': 'Duration',
        },
        'traffic_profile': 'ipv4_throughput_acl.yaml',
        'type': 'NSPerf',
        'nodes': {
            'tg__1': 'trafficgen_1.yardstick',
            'tg__0': 'trafficgen_0.yardstick',
            'vnf__0': 'vnf.yardstick',
        },
        'topology': 'vpe-tg-topology-baremetal.yaml',
    }

    context_cfg = {'nodes': {'tg__2':
                             {'member-vnf-index': '3',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_2.yardstick',
                              'vnfd-id-ref': 'tg__2',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens513f0',
                                       'vld_id': cgnapt_vnf.CgnaptApproxVnf.DOWNLINK,
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
                                       'vld_id': cgnapt_vnf.CgnaptApproxVnf.UPLINK,
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
                             'vnf__0':
                             {'name': 'vnf.yardstick',
                              'vnfd-id-ref': 'vnf__0',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens786f0',
                                       'vld_id': cgnapt_vnf.CgnaptApproxVnf.UPLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.19',
                                       'dst_mac': '00:00:00:00:00:04',
                                       'local_mac': '00:00:00:00:00:02',
                                       'dst_ip': '152.16.100.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens786f1',
                                       'vld_id': cgnapt_vnf.CgnaptApproxVnf.DOWNLINK,
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

    def setUp(self):
        self.scenario_cfg = deepcopy(self.SCENARIO_CFG)

    def test___init__(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        self.assertIsNone(cgnapt_approx_vnf._vnf_process)

    @mock.patch.object(process, 'check_if_process_failed')
    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    def test_collect_kpi(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        cgnapt_approx_vnf.scenario_helper.scenario_cfg = {
            'nodes': {cgnapt_approx_vnf.name: "mock"}
        }
        cgnapt_approx_vnf._vnf_process = mock.MagicMock(
            **{"is_alive.return_value": True, "exitcode": None})
        cgnapt_approx_vnf.q_in = mock.MagicMock()
        cgnapt_approx_vnf.q_out = mock.MagicMock()
        cgnapt_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        cgnapt_approx_vnf.resource = mock.Mock(
            autospec=resource.ResourceProfile)
        result = {
            'physical_node': 'mock_node',
            'packets_dropped': 0,
            'packets_fwd': 0,
            'packets_in': 0
        }
        with mock.patch.object(cgnapt_approx_vnf, 'get_stats',
                               return_value=''):
            self.assertEqual(result, cgnapt_approx_vnf.collect_kpi())

    @mock.patch.object(time, 'sleep')
    def test_vnf_execute_command(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        cgnapt_approx_vnf.q_in = mock.Mock()
        cgnapt_approx_vnf.q_out = mock.Mock()
        cgnapt_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        self.assertEqual("", cgnapt_approx_vnf.vnf_execute('quit'))

    def test_get_stats(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        with mock.patch.object(cgnapt_approx_vnf, 'vnf_execute') as mock_exec:
            mock_exec.return_value = 'output'
            self.assertEqual('output', cgnapt_approx_vnf.get_stats())

        mock_exec.assert_called_once_with('p cgnapt stats')

    def test_run_vcgnapt(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        cgnapt_approx_vnf.ssh_helper = mock.Mock()
        cgnapt_approx_vnf.setup_helper = mock.Mock()
        with mock.patch.object(cgnapt_approx_vnf, '_build_config'), \
                mock.patch.object(cgnapt_approx_vnf, '_build_run_kwargs'):
            cgnapt_approx_vnf._run()

        cgnapt_approx_vnf.ssh_helper.run.assert_called_once()
        cgnapt_approx_vnf.setup_helper.kill_vnf.assert_called_once()

    @mock.patch.object(ctx_base.Context, 'get_context_from_server')
    def test_instantiate(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        cgnapt_approx_vnf.deploy_helper = mock.MagicMock()
        cgnapt_approx_vnf.resource_helper = mock.MagicMock()
        cgnapt_approx_vnf._build_config = mock.MagicMock()
        self.scenario_cfg['vnf_options'] = {'acl': {'cfg': "",
                                                    'rules': ""}}
        cgnapt_approx_vnf.q_out.put("pipeline>")
        cgnapt_vnf.WAIT_TIME = 3
        self.scenario_cfg.update({"nodes": {"vnf__0": ""}})
        with mock.patch.object(cgnapt_approx_vnf, '_start_vnf'):
            self.assertIsNone(cgnapt_approx_vnf.instantiate(
                self.scenario_cfg, self.context_cfg))

    @mock.patch.object(time, 'sleep')
    def test__vnf_up_post(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.scenario_cfg['options'][name]['napt'] = 'static'
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        cgnapt_approx_vnf.vnf_execute = mock.Mock()
        cgnapt_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
        with mock.patch.object(cgnapt_approx_vnf, 'setup_helper') as \
                mock_setup_helper:
            mock_setup_helper._generate_ip_from_pool.return_value = ['ip1']
            mock_setup_helper._get_cgnapt_config.return_value = ['gw_ip1']
            cgnapt_approx_vnf._vnf_up_post()

    def test__vnf_up_post_short(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        cgnapt_approx_vnf = cgnapt_vnf.CgnaptApproxVnf(name, vnfd)
        cgnapt_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
        cgnapt_approx_vnf._vnf_up_post()
