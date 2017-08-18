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
from copy import deepcopy

from tests.unit import STL_MOCKS


SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.prox_vnf import ProxApproxVnf
    from tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh


NAME = "vnf__1"


@mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
class TestProxApproxVnf(unittest.TestCase):

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
                            'vld_id': '',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': '0',
                            'bandwidth': '10 Gbps',
                            'driver': "i40e",
                            'dst_ip': '152.16.100.20',
                            'local_iface_name': 'xe0',
                            'local_mac': '00:00:00:00:00:02',
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
                            'vld_id': '',
                            'driver': "i40e",
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': '1',
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_iface_name': 'xe1',
                            'local_mac': '00:00:00:00:00:01',
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

    SCENARIO_CFG = {
        'task_path': "",
        'nodes': {
            'tg__1': 'trafficgen_1.yardstick',
            'vnf__1': 'vnf.yardstick'},
        'runner': {
            'duration': 600, 'type': 'Duration'},
        'topology': 'prox-tg-topology-2.yaml',
        'traffic_profile': '../../traffic_profiles/prox_binsearch.yaml',
        'type': 'NSPerf',
        'options': {
            'tg__1': {'prox_args': {'-e': '',
                                    '-t': ''},
                      'prox_config': 'configs/l3-gen-2.cfg',
                      'prox_path':
                          '/root/dppd-PROX-v035/build/prox'},
            'vnf__1': {
                'prox_args': {'-t': ''},
                'prox_config': 'configs/l3-swap-2.cfg',
                'prox_path': '/root/dppd-PROX-v035/build/prox'}}}

    CONTEXT_CFG = {
        'nodes': {
            'tg__2': {
                'member-vnf-index': '3',
                'role': 'TrafficGen',
                'name': 'trafficgen_2.yardstick',
                'vnfd-id-ref': 'tg__2',
                'ip': '1.2.1.1',
                'interfaces': {
                    'xe0': {
                        'local_iface_name': 'ens513f0',
                        'vld_id': 'public',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.40.20',
                        'dst_mac': '00:00:00:00:00:01',
                        'local_mac': '00:00:00:00:00:03',
                        'dst_ip': '152.16.40.19',
                        'driver': 'ixgbe',
                        'vpci': '0000:02:00.0',
                        'dpdk_port_num': 0,
                    },
                    'xe1': {
                        'local_iface_name': 'ens513f1',
                        'netmask': '255.255.255.0',
                        'network': '202.16.100.0',
                        'local_ip': '202.16.100.20',
                        'local_mac': '00:1e:67:d0:60:5d',
                        'driver': 'ixgbe',
                        'vpci': '0000:02:00.1',
                        'dpdk_port_num': 1,
                    },
                },
                'password': 'r00t',
                'VNF model': 'l3fwd_vnf.yaml',
                'user': 'root',
            },
            'tg__1': {
                'member-vnf-index': '1',
                'role': 'TrafficGen',
                'name': 'trafficgen_1.yardstick',
                'vnfd-id-ref': 'tg__1',
                'ip': '1.2.1.1',
                'interfaces': {
                    'xe0': {
                        'local_iface_name': 'ens785f0',
                        'vld_id': 'private',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.100.20',
                        'dst_mac': '00:00:00:00:00:02',
                        'local_mac': '00:00:00:00:00:04',
                        'dst_ip': '152.16.100.19',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.0',
                        'dpdk_port_num': 0,
                    },
                    'xe1': {
                        'local_iface_name': 'ens785f1',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.100.21',
                        'local_mac': '00:00:00:00:00:01',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.1',
                        'dpdk_port_num': 1,
                    },
                },
                'password': 'r00t',
                'VNF model': 'tg_rfc2544_tpl.yaml',
                'user': 'root',
            },
            'vnf__1': {
                'name': 'vnf.yardstick',
                'vnfd-id-ref': 'vnf__1',
                'ip': '1.2.1.1',
                'interfaces': {
                    'xe0': {
                        'local_iface_name': 'ens786f0',
                        'vld_id': 'private',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.100.19',
                        'dst_mac': '00:00:00:00:00:04',
                        'local_mac': '00:00:00:00:00:02',
                        'dst_ip': '152.16.100.20',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.0',
                        'dpdk_port_num': 0,
                    },
                    'xe1': {
                        'local_iface_name': 'ens786f1',
                        'vld_id': 'public',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.40.19',
                        'dst_mac': '00:00:00:00:00:03',
                        'local_mac': '00:00:00:00:00:01',
                        'dst_ip': '152.16.40.20',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.1',
                        'dpdk_port_num': 1,
                    },
                },
                'routing_table': [
                    {
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'network': '152.16.100.20',
                        'if': 'xe0',
                    },
                    {
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'network': '152.16.40.20',
                        'if': 'xe1',
                    },
                ],
                'member-vnf-index': '2',
                'host': '1.2.1.1',
                'role': 'vnf',
                'user': 'root',
                'nd_route_tbl': [
                    {
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0',
                    },
                    {
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1',
                    },
                ],
                'password': 'r00t',
                'VNF model': 'prox_vnf.yaml',
            },
        },
    }

    @mock.patch(SSH_HELPER)
    def test___init__(self, ssh, mock_time):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        self.assertIsNone(prox_approx_vnf._vnf_process)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi_no_client(self, ssh, mock_time):
        mock_ssh(ssh)

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = None
        expected = {
            'packets_in': 0,
            'packets_dropped': 0,
            'packets_fwd': 0,
            'collect_stats': {'core': {}},
        }
        result = prox_approx_vnf.collect_kpi()
        self.assertEqual(result, expected)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, mock_time):
        mock_ssh(ssh)

        resource_helper = mock.MagicMock()
        resource_helper.execute.return_value = list(range(12))
        resource_helper.collect_kpi.return_value = {'core': {'result': 234}}

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = resource_helper

        expected = {
            'packets_in': 7,
            'packets_dropped': 1,
            'packets_fwd': 6,
            'collect_stats': {'core': {'result': 234}},
        }
        result = prox_approx_vnf.collect_kpi()
        self.assertEqual(result, expected)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi_error(self, ssh, mock_time):
        mock_ssh(ssh)

        resource_helper = mock.MagicMock()

        prox_approx_vnf = ProxApproxVnf(NAME, deepcopy(self.VNFD0))
        prox_approx_vnf.resource_helper = resource_helper
        prox_approx_vnf.vnfd_helper['vdu'][0]['external-interface'] = []

        with self.assertRaises(RuntimeError):
            prox_approx_vnf.collect_kpi()

    def _get_file_abspath(self, filename, mock_time):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch(SSH_HELPER)
    def test_run_prox(self, ssh, mock_time):
        mock_ssh(ssh)

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)

        filewrapper = mock.MagicMock()
        config_path = self.SCENARIO_CFG['options']["vnf__1"]["prox_config"]
        prox_path = self.SCENARIO_CFG['options']["vnf__1"]["prox_path"]
        prox_args = self.SCENARIO_CFG['options']["vnf__1"]["prox_args"]
        prox_approx_vnf.WAIT_TIME = 0
        prox_approx_vnf._run_prox(filewrapper, config_path, prox_path, prox_args)

        self.assertEqual(prox_approx_vnf.ssh_helper.run.call_args[0][0],
                         "sudo bash -c 'cd /root/dppd-PROX-v035/build; "
                         "/root/dppd-PROX-v035/build/prox -o cli -t  -f configs/l3-swap-2.cfg '")

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.CpuSysCores')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.find_relative_file')
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, mock_find, mock_cpu_sys_cores, mock_time):
        mock_ssh(ssh)

        mock_cpu_sys_cores.get_core_socket.return_value = {'0': '01234'}

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.ssh_helper = mock.MagicMock(
            **{"execute.return_value": (0, "", ""), "bin_path": ""})
        prox_approx_vnf.setup_helper._setup_resources = mock.MagicMock()
        prox_approx_vnf.setup_helper._find_used_drivers = mock.MagicMock()
        prox_approx_vnf.setup_helper.used_drivers = {}
        prox_approx_vnf.setup_helper.bound_pci = []
        prox_approx_vnf._run_prox = mock.MagicMock(return_value=0)
        prox_approx_vnf.resource_helper = mock.MagicMock()
        prox_approx_vnf.resource_helper.get_process_args.return_value = {
                    '-e': '',
                    '-t': '',
                }, 'configs/l3-gen-2.cfg', '/root/dppd-PROX-v035/build/prox'

        prox_approx_vnf.copy_to_target = mock.MagicMock()
        prox_approx_vnf.upload_prox_config = mock.MagicMock()
        prox_approx_vnf.generate_prox_config_file = mock.MagicMock()
        prox_approx_vnf.q_out.put("PROX started")
        prox_approx_vnf.WAIT_TIME = 0

        # if process it still running exitcode will be None
        expected = 0, None
        result = prox_approx_vnf.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG)
        self.assertIn(result, expected)

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_panic(self, ssh, mock_time):
        mock_ssh(ssh, exec_result=(1, "", ""))
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf._vnf_process = mock.MagicMock(**{"is_alive.return_value": True})
        prox_approx_vnf._run_prox = mock.Mock(return_value=0)
        prox_approx_vnf.WAIT_TIME = 0
        prox_approx_vnf.q_out.put("PANIC")
        with self.assertRaises(RuntimeError):
            prox_approx_vnf.wait_for_instantiate()

    @mock.patch(SSH_HELPER)
    def test_scale(self, ssh, mock_time):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        with self.assertRaises(NotImplementedError):
            prox_approx_vnf.scale('')

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, mock_socket, mock_time):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf._vnf_process = mock.MagicMock()
        prox_approx_vnf._vnf_process.terminate = mock.Mock()
        prox_approx_vnf.ssh_helper = mock.MagicMock()
        prox_approx_vnf.setup_helper = mock.Mock()
        prox_approx_vnf.resource_helper = mock.MagicMock()

        self.assertIsNone(prox_approx_vnf.terminate())

    @mock.patch(SSH_HELPER)
    def test__vnf_up_post(self, ssh, mock_time):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = resource_helper = mock.Mock()

        prox_approx_vnf._vnf_up_post()
        self.assertEqual(resource_helper.up_post.call_count, 1)


if __name__ == '__main__':
    unittest.main()
