# Copyright (c) 2017-2019 Intel Corporation
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

import unittest
import mock
import errno

from yardstick.tests import STL_MOCKS
from yardstick.common import exceptions as y_exceptions
from yardstick.network_services.vnf_generic.vnf.prox_irq import ProxIrqGen
from yardstick.network_services.vnf_generic.vnf.prox_irq import ProxIrqVNF
from yardstick.benchmark.contexts import base as ctx_base

SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf import prox_vnf
    from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh

VNF_NAME = "vnf__1"

class TestProxIrqVNF(unittest.TestCase):

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

    VNFD_0 = {
        'short-name': 'VpeVnf',
        'vdu': [
            {
                'routing_table': [
                    {
                        'network': '152.16.100.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'if': 'xe0'
                    },
                    {
                        'network': '152.16.40.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'if': 'xe1'
                    },
                ],
                'description': 'VPE approximation using DPDK',
                'name': 'vpevnf-baremetal',
                'nd_route_tbl': [
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0'
                    },
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1'
                    },
                ],
                'id': 'vpevnf-baremetal',
                'external-interface': [
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:03',
                            'vpci': '0000:05:00.0',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 0,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.20',
                            'local_mac': '00:00:00:00:00:01'
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0'
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.1',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 1,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_mac': '00:00:00:00:00:02'
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1'
                    },
                ],
            },
        ],
        'description': 'Vpe approximation using DPDK',
        'mgmt-interface': {
            'vdu-id': 'vpevnf-baremetal',
            'host': '1.1.1.1',
            'password': 'r00t',
            'user': 'root',
            'ip': '1.1.1.1'
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
        'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ]
        }
    }

    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64,
        },
    }

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
                        'vld_id': prox_vnf.ProxApproxVnf.DOWNLINK,
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
                        'vld_id': prox_vnf.ProxApproxVnf.UPLINK,
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
                        'vld_id': prox_vnf.ProxApproxVnf.UPLINK,
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
                        'vld_id': prox_vnf.ProxApproxVnf.DOWNLINK,
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

    def test___init__(self):
        prox_irq_vnf = ProxIrqVNF('vnf1', self.VNFD_0)

        self.assertEqual(prox_irq_vnf.name, 'vnf1')
        self.assertDictEqual(prox_irq_vnf.vnfd_helper, self.VNFD_0)

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        resource_helper = mock.MagicMock()

        resource_helper = mock.MagicMock()

        core_1 = {'bucket_1': 1, 'bucket_2': 2, 'bucket_3': 3, 'bucket_4': 4, 'bucket_5': 5,
                  'bucket_6': 6, 'bucket_7': 7, 'bucket_8': 8, 'bucket_9': 9, 'bucket_10': 10,
                  'bucket_11': 11, 'bucket_12': 12, 'bucket_0': 100, 'cpu': 1, 'max_irq': 12,
                  'overflow': 10}
        core_2 = {'bucket_1': 1, 'bucket_2': 2, 'bucket_3': 3, 'bucket_4': 4, 'bucket_5': 5,
                  'bucket_6': 0, 'bucket_7': 0, 'bucket_8': 0, 'bucket_9': 0, 'bucket_10': 0,
                  'bucket_11': 0, 'bucket_12': 0, 'bucket_0': 100, 'cpu': 2, 'max_irq': 12,
                  'overflow': 10}

        irq_data = {'core_1': core_1, 'core_2': core_2}
        resource_helper.execute.return_value = (irq_data)

        build_config_file = mock.MagicMock()
        build_config_file.return_value = None

        prox_irq_vnf = ProxIrqVNF(VNF_NAME, vnfd)

        startup = ["global", [["eal", "-4"]]]
        master_0 = ["core 0", [["mode", "master"]]]
        core_1 = ["core 1", [["mode", "irq"]]]
        core_2 = ["core 2", [["mode", "irq"], ["task", "2"]]]

        prox_irq_vnf.setup_helper._prox_config_data = \
            [startup, master_0, core_1, core_2]

        prox_irq_vnf.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        prox_irq_vnf.resource_helper = resource_helper
        prox_irq_vnf.setup_helper.build_config_file = build_config_file

        result = prox_irq_vnf.collect_kpi()
        self.assertDictEqual(result["collect_stats"], {})

        result = prox_irq_vnf.collect_kpi()
        self.assertFalse('bucket_10' in result["collect_stats"]['core_2'])
        self.assertFalse('bucket_11' in result["collect_stats"]['core_2'])
        self.assertFalse('bucket_12' in result["collect_stats"]['core_2'])
        self.assertEqual(result["collect_stats"]['core_2']['max_irq'], 12)


    @mock.patch(SSH_HELPER)
    def test_vnf_execute_oserror(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        prox_irq_vnf = ProxIrqVNF(VNF_NAME, vnfd)
        prox_irq_vnf.resource_helper = resource_helper = mock.Mock()

        resource_helper.execute.side_effect = OSError(errno.EPIPE, "")
        prox_irq_vnf.vnf_execute("", _ignore_errors=True)

        resource_helper.execute.side_effect = OSError(errno.ESHUTDOWN, "")
        prox_irq_vnf.vnf_execute("", _ignore_errors=True)

        resource_helper.execute.side_effect = OSError(errno.EADDRINUSE, "")
        with self.assertRaises(OSError):
            prox_irq_vnf.vnf_execute("", _ignore_errors=True)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]

        mock_ssh(ssh, exec_result=(1, "", ""))
        prox_irq_vnf = ProxIrqVNF(VNF_NAME, vnfd)

        prox_irq_vnf._terminated = mock.MagicMock()
        prox_irq_vnf._traffic_process = mock.MagicMock()
        prox_irq_vnf._traffic_process.terminate = mock.Mock()
        prox_irq_vnf.ssh_helper = mock.MagicMock()
        prox_irq_vnf.setup_helper = mock.MagicMock()
        prox_irq_vnf.resource_helper = mock.MagicMock()
        prox_irq_vnf._vnf_wrapper.setup_helper = mock.MagicMock()
        prox_irq_vnf._vnf_wrapper._vnf_process = mock.MagicMock(**{"is_alive.return_value": False})
        prox_irq_vnf._vnf_wrapper.resource_helper = mock.MagicMock()

        prox_irq_vnf._run_prox = mock.Mock(return_value=0)
        prox_irq_vnf.q_in = mock.Mock()
        prox_irq_vnf.q_out = mock.Mock()

        self.assertIsNone(prox_irq_vnf.terminate())

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_panic(self, ssh, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]

        mock_ssh(ssh, exec_result=(1, "", ""))
        prox_irq_vnf = ProxIrqVNF(VNF_NAME, vnfd)

        prox_irq_vnf._terminated = mock.MagicMock()
        prox_irq_vnf._traffic_process = mock.MagicMock()
        prox_irq_vnf._traffic_process.terminate = mock.Mock()
        prox_irq_vnf.ssh_helper = mock.MagicMock()
        prox_irq_vnf.setup_helper = mock.MagicMock()
        prox_irq_vnf.resource_helper = mock.MagicMock()
        prox_irq_vnf._vnf_wrapper.setup_helper = mock.MagicMock()
        prox_irq_vnf._vnf_wrapper._vnf_process = mock.MagicMock(**{"is_alive.return_value": False})
        prox_irq_vnf._vnf_wrapper.resource_helper = mock.MagicMock()

        prox_irq_vnf._run_prox = mock.Mock(return_value=0)
        prox_irq_vnf.q_in = mock.Mock()
        prox_irq_vnf.q_out = mock.Mock()
        prox_irq_vnf.WAIT_TIME = 0
        with self.assertRaises(RuntimeError):
            prox_irq_vnf.wait_for_instantiate()

class TestProxIrqGen(unittest.TestCase):

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

    VNFD_0 = {
        'short-name': 'VpeVnf',
        'vdu': [
            {
                'routing_table': [
                    {
                        'network': '152.16.100.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'if': 'xe0'
                    },
                    {
                        'network': '152.16.40.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'if': 'xe1'
                    },
                ],
                'description': 'VPE approximation using DPDK',
                'name': 'vpevnf-baremetal',
                'nd_route_tbl': [
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0'
                    },
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1'
                    },
                ],
                'id': 'vpevnf-baremetal',
                'external-interface': [
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:03',
                            'vpci': '0000:05:00.0',
                            'driver': 'i40e',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 0,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.20',
                            'local_mac': '00:00:00:00:00:01'
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0'
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.1',
                            'driver': 'ixgbe',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 1,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_mac': '00:00:00:00:00:02'
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1'
                    },
                ],
            },
        ],
        'description': 'Vpe approximation using DPDK',
        'mgmt-interface': {
            'vdu-id': 'vpevnf-baremetal',
            'host': '1.1.1.1',
            'password': 'r00t',
            'user': 'root',
            'ip': '1.1.1.1'
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
        'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ],
        },
    }

    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64,
        },
    }

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
                        'vld_id': prox_vnf.ProxApproxVnf.DOWNLINK,
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
                        'vld_id': prox_vnf.ProxApproxVnf.UPLINK,
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
                        'vld_id': prox_vnf.ProxApproxVnf.UPLINK,
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
                        'vld_id': prox_vnf.ProxApproxVnf.DOWNLINK,
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


    def test__check_status(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)

        with self.assertRaises(NotImplementedError):
            prox_irq_gen._check_status()

    def test_listen_traffic(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)

        prox_irq_gen.listen_traffic(mock.Mock())

    def test_verify_traffic(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)

        prox_irq_gen.verify_traffic(mock.Mock())

    mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        prox_traffic_gen = ProxIrqGen(VNF_NAME, vnfd)
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

    def test__wait_for_process(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)
        with mock.patch.object(prox_irq_gen, '_check_status',
                               return_value=0) as mock_status, \
                mock.patch.object(prox_irq_gen, '_tg_process') as mock_proc:
            mock_proc.is_alive.return_value = True
            mock_proc.exitcode = 234
            self.assertEqual(prox_irq_gen._wait_for_process(), 234)
            mock_proc.is_alive.assert_called_once()
            mock_status.assert_called_once()

    def test__wait_for_process_not_alive(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)
        with mock.patch.object(prox_irq_gen, '_tg_process') as mock_proc:
            mock_proc.is_alive.return_value = False
            self.assertRaises(RuntimeError, prox_irq_gen._wait_for_process)
            mock_proc.is_alive.assert_called_once()

    def test__wait_for_process_delayed(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)
        with mock.patch.object(prox_irq_gen, '_check_status',
                               side_effect=[1, 0]) as mock_status, \
                mock.patch.object(prox_irq_gen,
                                  '_tg_process') as mock_proc:
            mock_proc.is_alive.return_value = True
            mock_proc.exitcode = 234
            self.assertEqual(prox_irq_gen._wait_for_process(), 234)
            mock_proc.is_alive.assert_has_calls([mock.call(), mock.call()])
            mock_status.assert_has_calls([mock.call(), mock.call()])

    def test_scale(self):
        prox_irq_gen = ProxIrqGen('tg1', self.VNFD_0)
        self.assertRaises(y_exceptions.FunctionNotImplemented,
                          prox_irq_gen.scale)

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        resource_helper = mock.MagicMock()

        core_1 = {'bucket_1': 1, 'bucket_2': 2, 'bucket_3': 3, 'bucket_4': 4, 'bucket_5': 5,
                  'bucket_6': 6, 'bucket_7': 7, 'bucket_8': 8, 'bucket_9': 9, 'bucket_10': 10,
                  'bucket_11': 11, 'bucket_12': 12, 'bucket_0': 100, 'cpu': 1, 'max_irq': 12,
                  'overflow': 10}
        core_2 = {'bucket_1': 1, 'bucket_2': 2, 'bucket_3': 3, 'bucket_4': 4, 'bucket_5': 5,
                  'bucket_6': 0, 'bucket_7': 0, 'bucket_8': 0, 'bucket_9': 0, 'bucket_10': 0,
                  'bucket_11': 0, 'bucket_12': 0, 'bucket_0': 100, 'cpu': 2, 'max_irq': 12,
                  'overflow': 10}

        irq_data = {'core_1': core_1, 'core_2': core_2}
        resource_helper.sut.irq_core_stats.return_value = (irq_data)

        build_config_file = mock.MagicMock()
        build_config_file.return_value = None

        prox_irq_gen = ProxIrqGen(VNF_NAME, vnfd)

        startup = ["global", [["eal", "-4"]]]
        master_0 = ["core 0", [["mode", "master"]]]
        core_1 = ["core 1", [["mode", "irq"]]]
        core_2 = ["core 2", [["mode", "irq"], ["task", "2"]]]

        prox_irq_gen.setup_helper._prox_config_data = \
            [startup, master_0, core_1, core_2]

        prox_irq_gen.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        prox_irq_gen.resource_helper = resource_helper
        prox_irq_gen.setup_helper.build_config_file = build_config_file

        result = prox_irq_gen.collect_kpi()
        self.assertDictEqual(result["collect_stats"], {})

        result = prox_irq_gen.collect_kpi()
        self.assertFalse('bucket_10' in result["collect_stats"]['core_2'])
        self.assertFalse('bucket_11' in result["collect_stats"]['core_2'])
        self.assertFalse('bucket_12' in result["collect_stats"]['core_2'])
        self.assertEqual(result["collect_stats"]['core_2']['max_irq'], 12)
