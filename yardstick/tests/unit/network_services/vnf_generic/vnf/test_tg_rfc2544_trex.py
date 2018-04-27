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

from yardstick.tests import STL_MOCKS
SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.tg_rfc2544_trex import TrexTrafficGenRFC, \
        TrexRfcResourceHelper
    from yardstick.network_services.vnf_generic.vnf import tg_rfc2544_trex
    from yardstick.network_services.traffic_profile.base import TrafficProfile
    from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base \
        import FileAbsPath, mock_ssh

MODULE_PATH = FileAbsPath(__file__)
get_file_abspath = MODULE_PATH.get_path


class TestTrexRfcResouceHelper(unittest.TestCase):

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.MultiPortConfig')
    @mock.patch("yardstick.network_services.vnf_generic.vnf.tg_rfc2544_trex.time")
    @mock.patch(SSH_HELPER)
    def test__run_traffic_once(self, ssh, *_):
        mock_ssh(ssh)

        mock_traffic_profile = mock.MagicMock(autospec=TrafficProfile,
                                              **{'get_drop_percentage.return_value': {}})
        sut = TrexRfcResourceHelper(mock.MagicMock(), mock.MagicMock())
        sut.client = mock.MagicMock()
        sut._run_traffic_once(mock_traffic_profile)


class TestTrexTrafficGenRFC(unittest.TestCase):

    VNFD_0 = {
        'short-name': 'VpeVnf',
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
                'description': 'VPE approximation using DPDK',
                'name': 'vpevnf-baremetal',
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
                'id': 'vpevnf-baremetal',
                'external-interface': [
                    {
                        'virtual-interface': {
                            'ifname': 'xe0',
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.0',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'vld_id': 'uplink_0',
                            'dpdk_port_num': 0,
                            'bandwidth': '10 Gbps',
                            'driver': "i40e",
                            'dst_ip': '152.16.100.20',
                            'local_iface_name': 'xe0',
                            'local_mac': '00:00:00:00:00:01',
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0',
                    },
                    {
                        'virtual-interface': {
                            'ifname': 'xe1',
                            'dst_mac': '00:00:00:00:00:03',
                            'vpci': '0000:05:00.1',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'driver': "i40e",
                            'netmask': '255.255.255.0',
                            'vld_id': 'downlink_0',
                            'dpdk_port_num': 1,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_iface_name': 'xe1',
                            'local_mac': '00:00:00:00:00:02'
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1',
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
            'ip': '1.1.1.1',
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
        'id': 'VpeApproxVnf',
        'name': 'VPEVnfSsh',
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

    TC_YAML = {
        'scenarios': [
            {
                'tc_options': {
                    'rfc2544': {
                        'allowed_drop_rate': '0.8 - 1',
                    },
                },
                'runner': {
                    'duration': 400,
                    'interval': 35,
                    'type': 'Duration',
                },
                'traffic_options': {
                    'flow': 'ipv4_1flow_Packets_vpe.yaml',
                    'imix': 'imix_voice.yaml',
                },
                'vnf_options': {
                    'vpe': {
                        'cfg': 'vpe_config',
                    },
                },
                'traffic_profile': 'ipv4_throughput_vpe.yaml',
                'type': 'NSPerf',
                'nodes': {
                    'tg__1': 'trafficgen_1.yardstick',
                    'vnf__1': 'vnf.yardstick',
                },
                'topology': 'vpe_vnf_topology.yaml',
            },
        ],
        'context': {
            'nfvi_type': 'baremetal',
            'type': 'Node',
            'name': 'yardstick',
            'file': '/etc/yardstick/nodes/pod.yaml',
        },
        'schema': 'yardstick:task:0.1',
    }

    @mock.patch(SSH_HELPER)
    def test___init__(self, ssh):
        mock_ssh(ssh)
        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        self.assertIsNotNone(trex_traffic_gen.resource_helper._terminated.value)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh):
        mock_ssh(ssh)
        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        self.assertEqual(trex_traffic_gen.collect_kpi(), {})

    @mock.patch(SSH_HELPER)
    def test_listen_traffic(self, ssh):
        mock_ssh(ssh)
        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        self.assertIsNone(trex_traffic_gen.listen_traffic({}))

    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen.resource_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()

        scenario_cfg = {
            "tc": "tc_baremetal_rfc2544_ipv4_1flow_64B",
            "topology": 'nsb_test_case.yaml',
            'options': {
                'packetsize': 64,
                'traffic_type': 4,
                'rfc2544': {
                    'allowed_drop_rate': '0.8 - 1',
                },
                'vnf__1': {
                    'rules': 'acl_1rule.yaml',
                    'vnf_config': {
                        'lb_config': 'SW',
                        'lb_count': 1,
                        'worker_config': '1C/1T',
                        'worker_threads': 1
                    },
                },
            },
        }
        tg_rfc2544_trex.WAIT_TIME = 3
        scenario_cfg.update({"nodes": ["tg_1", "vnf_1"]})
        self.assertIsNone(trex_traffic_gen.instantiate(scenario_cfg, {}))

    @mock.patch(SSH_HELPER)
    def test_instantiate_error(self, ssh):
        mock_ssh(ssh, exec_result=(1, "", ""))

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        trex_traffic_gen.resource_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()
        scenario_cfg = {
            "tc": "tc_baremetal_rfc2544_ipv4_1flow_64B",
            "nodes": [
                "tg_1",
                "vnf_1",
            ],
            "topology": 'nsb_test_case.yaml',
            'options': {
                'packetsize': 64,
                'traffic_type': 4,
                'rfc2544': {
                    'allowed_drop_rate': '0.8 - 1',
                },
                'vnf__1': {
                    'rules': 'acl_1rule.yaml',
                    'vnf_config': {
                        'lb_config': 'SW',
                        'lb_count': 1,
                        'worker_config': '1C/1T',
                        'worker_threads': 1,
                    },
                },
            },
        }
        trex_traffic_gen.instantiate(scenario_cfg, {})

    @mock.patch(SSH_HELPER)
    def test__start_server(self, ssh):
        mock_ssh(ssh)
        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        trex_traffic_gen.resource_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen._start_server())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.tg_rfc2544_trex.time")
    @mock.patch(SSH_HELPER)
    def test__generate_trex_cfg(self, ssh, _):
        mock_ssh(ssh)

        trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.resource_helper.generate_cfg())

    def test_terminate(self):
        with mock.patch(SSH_HELPER) as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            trex_traffic_gen = TrexTrafficGenRFC('vnf1', self.VNFD_0)
            trex_traffic_gen.resource_helper = mock.MagicMock()
            self.assertIsNone(trex_traffic_gen.terminate())
