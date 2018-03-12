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

import errno
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
                            'vld_id': 'downlink_0',
                            'ifname': 'xe1',
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
                            'vld_id': 'uplink_0',
                            'ifname': 'xe1',
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
                'curr_packets_fwd',
                'curr_packets_in'
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
                        'vld_id': ProxApproxVnf.DOWNLINK,
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
                        'vld_id': ProxApproxVnf.UPLINK,
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
                        'vld_id': ProxApproxVnf.UPLINK,
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
                        'vld_id': ProxApproxVnf.DOWNLINK,
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
    def test___init__(self, ssh, *args):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        self.assertIsNone(prox_approx_vnf._vnf_process)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi_no_client(self, ssh, *args):
        mock_ssh(ssh)

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = None
        expected = {
            'packets_in': 0,
            'packets_dropped': 0,
            'packets_fwd': 0,
            'collect_stats': {'core': {}}
        }
        result = prox_approx_vnf.collect_kpi()
        self.assertEqual(result, expected)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        resource_helper = mock.MagicMock()
        resource_helper.execute.return_value = list(range(12))
        resource_helper.collect_collectd_kpi.return_value = {'core': {'result': 234}}

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = resource_helper

        expected = {
            'packets_in': 6,
            'packets_dropped': 1,
            'packets_fwd': 7,
            'collect_stats': {'core': {'result': 234}},
        }
        result = prox_approx_vnf.collect_kpi()
        self.assertEqual(result['packets_in'], expected['packets_in'])
        self.assertEqual(result['packets_dropped'], expected['packets_dropped'])
        self.assertEqual(result['packets_fwd'], expected['packets_fwd'])
        self.assertNotEqual(result['packets_fwd'], 0)
        self.assertNotEqual(result['packets_fwd'], 0)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi_error(self, ssh, *args):
        mock_ssh(ssh)

        resource_helper = mock.MagicMock()

        prox_approx_vnf = ProxApproxVnf(NAME, deepcopy(self.VNFD0))
        prox_approx_vnf.resource_helper = resource_helper
        prox_approx_vnf.vnfd_helper['vdu'][0]['external-interface'] = []
        prox_approx_vnf.vnfd_helper.port_pairs.interfaces = []

        with self.assertRaises(RuntimeError):
            prox_approx_vnf.collect_kpi()

    def _get_file_abspath(self, filename, *args):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch('yardstick.common.utils.open', create=True)
    @mock.patch('yardstick.benchmark.scenarios.networking.vnf_generic.open', create=True)
    @mock.patch('yardstick.network_services.helpers.iniparser.open', create=True)
    @mock.patch(SSH_HELPER)
    def test_run_prox(self, ssh, *_):
        mock_ssh(ssh)

        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.scenario_helper.scenario_cfg = self.SCENARIO_CFG
        prox_approx_vnf.ssh_helper.join_bin_path.return_value = '/tool_path12/tool_file34'
        prox_approx_vnf.setup_helper.remote_path = 'configs/file56.cfg'

        expected = "sudo bash -c 'cd /tool_path12; " \
                   "/tool_path12/tool_file34 -o cli -t  -f /tmp/l3-swap-2.cfg '"

        prox_approx_vnf._run()
        result = prox_approx_vnf.ssh_helper.run.call_args[0][0]
        self.assertEqual(result, expected)

    @mock.patch(SSH_HELPER)
    def bad_test_instantiate(self, *args):
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.scenario_helper = mock.MagicMock()
        prox_approx_vnf.setup_helper = mock.MagicMock()
        # we can't mock super
        prox_approx_vnf.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG)
        prox_approx_vnf.setup_helper.build_config.assert_called_once()

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_panic(self, ssh, *args):
        mock_ssh(ssh, exec_result=(1, "", ""))
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf._vnf_process = mock.MagicMock(**{"is_alive.return_value": True})
        prox_approx_vnf._run_prox = mock.Mock(return_value=0)
        prox_approx_vnf.WAIT_TIME = 0
        prox_approx_vnf.q_out.put("PANIC")
        with self.assertRaises(RuntimeError):
            prox_approx_vnf.wait_for_instantiate()

    @mock.patch('yardstick.network_services.vnf_generic.vnf.prox_helpers.socket')
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf._vnf_process = mock.MagicMock()
        prox_approx_vnf._vnf_process.terminate = mock.Mock()
        prox_approx_vnf.ssh_helper = mock.MagicMock()
        prox_approx_vnf.setup_helper = mock.Mock()
        prox_approx_vnf.resource_helper = mock.MagicMock()

        self.assertIsNone(prox_approx_vnf.terminate())

    @mock.patch(SSH_HELPER)
    def test__vnf_up_post(self, ssh, *args):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = resource_helper = mock.Mock()

        prox_approx_vnf._vnf_up_post()
        resource_helper.up_post.assert_called_once()

    @mock.patch(SSH_HELPER)
    def test_vnf_execute_oserror(self, ssh, *args):
        mock_ssh(ssh)
        prox_approx_vnf = ProxApproxVnf(NAME, self.VNFD0)
        prox_approx_vnf.resource_helper = resource_helper = mock.Mock()

        resource_helper.execute.side_effect = OSError(errno.EPIPE, "")
        prox_approx_vnf.vnf_execute("", _ignore_errors=True)

        resource_helper.execute.side_effect = OSError(errno.ESHUTDOWN, "")
        prox_approx_vnf.vnf_execute("", _ignore_errors=True)

        resource_helper.execute.side_effect = OSError(errno.EADDRINUSE, "")
        with self.assertRaises(OSError):
            prox_approx_vnf.vnf_execute("", _ignore_errors=True)
