# Copyright (c) 2017 Intel Corporation
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

from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh
from tests.unit import STL_MOCKS


SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'
NAME = 'vnf__1'

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.tg_prox import ProxTrafficGen
    from yardstick.network_services.traffic_profile.base import TrafficProfile


@mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.time')
class TestProxTrafficGen(unittest.TestCase):
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
                            'dpdk_port_num': 0,
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
                            'dpdk_port_num': 1,
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
                        'vld_id': ProxTrafficGen.DOWNLINK,
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
                        'vld_id': ProxTrafficGen.UPLINK,
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
                        'vld_id': ProxTrafficGen.UPLINK,
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
                        'vld_id': ProxTrafficGen.DOWNLINK,
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

    TRAFFIC_PROFILE = {
        'description': 'Binary search for max no-drop throughput over given packet sizes',
        'name': 'prox_binsearch',
        'schema': 'nsb:traffic_profile:0.1',
        'traffic_profile': {
            'duration': 5,
            'lower_bound': 0.0,
            'packet_sizes': [64, 65],
            'test_precision': 1.0,
            'tolerated_loss': 0.0,
            'traffic_type': 'ProxBinSearchProfile',
            'upper_bound': 100.0}}

    @mock.patch(SSH_HELPER)
    def test___init__(self, ssh, *args):
        mock_ssh(ssh)
        prox_traffic_gen = ProxTrafficGen(NAME, self.VNFD0)
        self.assertIsNone(prox_traffic_gen._tg_process)
        self.assertIsNone(prox_traffic_gen._traffic_process)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        prox_traffic_gen = ProxTrafficGen(NAME, self.VNFD0)
        prox_traffic_gen._vnf_wrapper.resource_helper.resource = mock.MagicMock(
            **{"self.check_if_system_agent_running.return_value": [False]})
        prox_traffic_gen._vnf_wrapper.vnf_execute = mock.Mock(return_value="")
        self.assertEqual({}, prox_traffic_gen.collect_kpi())


    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.find_relative_file')
    @mock.patch(
        'yardstick.network_services.vnf_generic.vnf.sample_vnf.CpuSysCores')
    @mock.patch(SSH_HELPER)
    def bad_test_instantiate(self, ssh, mock_cpu_sys_cores, *args):
        mock_ssh(ssh)

        mock_cpu_sys_cores.get_core_socket.return_value = {'0': '01234'}

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        prox_traffic_gen = ProxTrafficGen(NAME, vnfd)
        ssh_helper = mock.MagicMock(
            **{"execute.return_value": (0, "", ""), "bin_path": ""})
        prox_traffic_gen.ssh_helper = ssh_helper
        prox_traffic_gen.setup_helper.dpdk_bind_helper.ssh_helper = ssh_helper
        prox_traffic_gen.setup_helper._setup_resources = mock.MagicMock()
        prox_traffic_gen.setup_hugepages = mock.MagicMock()
        prox_traffic_gen.generate_prox_config_file = mock.MagicMock()
        prox_traffic_gen.upload_prox_config = mock.MagicMock()
        prox_traffic_gen.setup_helper._find_used_drivers = mock.MagicMock()
        prox_traffic_gen.setup_helper.used_drivers = {}
        prox_traffic_gen.setup_helper.bound_pci = []
        prox_traffic_gen._start_server = mock.Mock(return_value=0)
        prox_traffic_gen._tg_process = mock.MagicMock()
        prox_traffic_gen._tg_process.start = mock.Mock()
        prox_traffic_gen._tg_process.exitcode = 0
        prox_traffic_gen._tg_process._is_alive = mock.Mock(return_value=1)
        prox_traffic_gen.ssh_helper = mock.MagicMock()
        prox_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        scenario_cfg = {
            'task_path': '',
            'options': {'tg__1': {'prox_args': {'-e': '',
                                                '-t': ''},
                                  'prox_config': 'configs/l3-gen-2.cfg',
                                  'prox_path': '/root/dppd-PROX-v035/build/prox'},
                        'vnf__1': {'prox_args': {'-t': ''},
                                   'prox_config': 'configs/l3-swap-2.cfg',
                                   'prox_path': '/root/dppd-PROX-v035/build/prox'}
                        }
        }
        prox_traffic_gen.instantiate(scenario_cfg, {})

    @mock.patch(SSH_HELPER)
    def test__traffic_runner(self, ssh, *args):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.execute_traffic.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sut = ProxTrafficGen(NAME, vnfd)
        sut._get_socket = mock.MagicMock()
        sut.ssh_helper = mock.Mock()
        sut.ssh_helper.run = mock.Mock()
        sut.setup_helper.prox_config_dict = {}
        sut._connect_client = mock.Mock(autospec=STLClient)
        sut._connect_client.get_stats = mock.Mock(return_value="0")
        sut._traffic_runner(mock_traffic_profile)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    @mock.patch(SSH_HELPER)
    def test_listen_traffic(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        prox_traffic_gen = ProxTrafficGen(NAME, vnfd)
        self.assertIsNone(prox_traffic_gen.listen_traffic(mock.Mock()))

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        prox_traffic_gen = ProxTrafficGen(NAME, vnfd)
        prox_traffic_gen._terminated = mock.MagicMock()
        prox_traffic_gen._traffic_process = mock.MagicMock()
        prox_traffic_gen._traffic_process.terminate = mock.Mock()
        prox_traffic_gen.ssh_helper = mock.MagicMock()
        prox_traffic_gen.setup_helper = mock.MagicMock()
        prox_traffic_gen.resource_helper = mock.MagicMock()
        prox_traffic_gen._vnf_wrapper.setup_helper = mock.MagicMock()
        prox_traffic_gen._vnf_wrapper._vnf_process = mock.MagicMock()
        prox_traffic_gen._vnf_wrapper.resource_helper = mock.MagicMock()
        self.assertIsNone(prox_traffic_gen.terminate())
