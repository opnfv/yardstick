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

import mock
import unittest

from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import tg_rfc2544_trex


class TestTrexRfcResouceHelper(unittest.TestCase):

    # @mock.patch('yardstick.network_services.helpers.samplevnf_helper.MultiPortConfig')
    # @mock.patch("yardstick.network_services.vnf_generic.vnf.tg_rfc2544_trex.time")
    # @mock.patch.object(sample_vnf, 'VnfSshHelper')
    # def test__run_traffic_once(self, *args):
    #     mock_traffic_profile = mock.MagicMock(autospec=TrafficProfile,
    #                                           **{'get_drop_percentage.return_value': {}})
    #     sut = TrexRfcResourceHelper(mock.MagicMock(), mock.MagicMock())
    #     sut.client = mock.MagicMock()
    #     sut._run_traffic_once(mock_traffic_profile)


# def _run_traffic_once(self, traffic_profile):
#     self.client_started.value = 1
#     ports, port_pg_id = traffic_profile.execute_traffic(self)
#
#     samples = []
#     timeout = int(
#         traffic_profile.config.duration) - self.TRANSIENT_PERIOD
#     time.sleep(self.TRANSIENT_PERIOD)
#     for _ in utils.Timer(timeout=timeout):
#         samples.append(self._get_samples(ports, port_pg_id=port_pg_id))
#         time.sleep(self.SAMPLING_PERIOD)
#
#     traffic_profile.stop_traffic(self)
#     output = traffic_profile.get_drop_percentage(
#         samples, self.rfc2544_helper.tolerance_low,
#         self.rfc2544_helper.tolerance_high,
#         self.rfc2544_helper.correlated_traffic)
#     self._queue.put(output)
    def test__run_traffic_once(self):
        pass



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

    def setUp(self):
        self._mock_ssh_helper = mock.patch.object(sample_vnf, 'VnfSshHelper')
        self.mock_ssh_helper = self._mock_ssh_helper.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_ssh_helper.stop()

    def test___init__(self):
        trex_traffic_gen = tg_rfc2544_trex.TrexTrafficGenRFC('vnf1', self.VNFD_0)
        self.assertIsNotNone(trex_traffic_gen.resource_helper._terminated.value)

    def test_instantiate(self):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        trex_traffic_gen = tg_rfc2544_trex.TrexTrafficGenRFC('vnf1', self.VNFD_0)
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

    def test_instantiate_error(self):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        trex_traffic_gen = tg_rfc2544_trex.TrexTrafficGenRFC('vnf1', self.VNFD_0)
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
