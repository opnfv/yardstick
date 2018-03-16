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

from copy import deepcopy
import os
import sys

import mock
import unittest

from yardstick import tests
from yardstick.common import utils
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.traffic_profile import base
from yardstick.network_services.vnf_generic import vnfdgen
from yardstick.error import IncorrectConfig
from yardstick.network_services.vnf_generic.vnf.base import GenericTrafficGen
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF


stl_patch = mock.patch.dict(sys.modules, tests.STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.benchmark.scenarios.networking import vnf_generic

# pylint: disable=unused-argument
# disable this for now because I keep forgetting mock patch arg ordering


COMPLETE_TREX_VNFD = {
    'vnfd:vnfd-catalog': {
        'vnfd': [
            {
                'benchmark': {
                    'kpi': [
                        'rx_throughput_fps',
                        'tx_throughput_fps',
                        'tx_throughput_mbps',
                        'rx_throughput_mbps',
                        'tx_throughput_pc_linerate',
                        'rx_throughput_pc_linerate',
                        'min_latency',
                        'max_latency',
                        'avg_latency',
                    ],
                },
                'connection-point': [
                    {
                        'name': 'xe0',
                        'type': 'VPORT',
                    },
                    {
                        'name': 'xe1',
                        'type': 'VPORT',
                    },
                ],
                'description': 'TRex stateless traffic generator for RFC2544',
                'id': 'TrexTrafficGen',
                'mgmt-interface': {
                    'ip': '1.1.1.1',
                    'password': 'berta',
                    'user': 'berta',
                    'vdu-id': 'trexgen-baremetal',
                },
                'name': 'trexgen',
                'short-name': 'trexgen',
                'class-name': 'TrexTrafficGen',
                'vdu': [
                    {
                        'description': 'TRex stateless traffic generator for RFC2544',
                        'external-interface': [
                            {
                                'name': 'xe0',
                                'virtual-interface': {
                                    'bandwidth': '10 Gbps',
                                    'dst_ip': '1.1.1.1',
                                    'dst_mac': '00:01:02:03:04:05',
                                    'local_ip': '1.1.1.2',
                                    'local_mac': '00:01:02:03:05:05',
                                    'type': 'PCI-PASSTHROUGH',
                                    'netmask': "255.255.255.0",
                                    'driver': 'i40',
                                    'vpci': '0000:00:10.2',
                                },
                                'vnfd-connection-point-ref': 'xe0',
                            },
                            {
                                'name': 'xe1',
                                'virtual-interface': {
                                    'bandwidth': '10 Gbps',
                                    'dst_ip': '2.1.1.1',
                                    'dst_mac': '00:01:02:03:04:06',
                                    'local_ip': '2.1.1.2',
                                    'local_mac': '00:01:02:03:05:06',
                                    'type': 'PCI-PASSTHROUGH',
                                    'netmask': "255.255.255.0",
                                    'driver': 'i40',
                                    'vpci': '0000:00:10.1',
                                },
                                'vnfd-connection-point-ref': 'xe1',
                            },
                        ],
                        'id': 'trexgen-baremetal',
                        'name': 'trexgen-baremetal',
                    },
                ],
            },
        ],
    },
}

IP_ADDR_SHOW = """
28: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP \
group default qlen 1000
    link/ether 90:e2:ba:a7:6a:c8 brd ff:ff:ff:ff:ff:ff
    inet 1.1.1.1/8 brd 1.255.255.255 scope global eth1
    inet6 fe80::92e2:baff:fea7:6ac8/64 scope link
       valid_lft forever preferred_lft forever
29: eth5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP \
group default qlen 1000
    link/ether 90:e2:ba:a7:6a:c9 brd ff:ff:ff:ff:ff:ff
    inet 2.1.1.1/8 brd 2.255.255.255 scope global eth5
    inet6 fe80::92e2:baff:fea7:6ac9/64 scope link tentative
       valid_lft forever preferred_lft forever
"""

SYS_CLASS_NET = """
lrwxrwxrwx 1 root root 0 sie 10 14:16 eth1 -> \
../../devices/pci0000:80/0000:80:02.2/0000:84:00.1/net/eth1
lrwxrwxrwx 1 root root 0 sie  3 10:37 eth2 -> \
../../devices/pci0000:00/0000:00:01.1/0000:84:00.2/net/eth5
"""

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


class TestNetworkServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.tg__1 = {
            'name': 'trafficgen_1.yardstick',
            'ip': '10.10.10.11',
            'role': 'TrafficGen',
            'user': 'root',
            'password': 'r00t',
            'interfaces': {
                'xe0': {
                    'netmask': '255.255.255.0',
                    'local_ip': '152.16.100.20',
                    'local_mac': '00:00:00:00:00:01',
                    'driver': 'i40e',
                    'vpci': '0000:07:00.0',
                    'dpdk_port_num': 0,
                },
                'xe1': {
                    'netmask': '255.255.255.0',
                    'local_ip': '152.16.40.20',
                    'local_mac': '00:00:00:00:00:02',
                    'driver': 'i40e',
                    'vpci': '0000:07:00.1',
                    'dpdk_port_num': 1,
                },
            },
        }

        self.vnf__1 = {
            'name': 'vnf.yardstick',
            'ip': '10.10.10.12',
            'host': '10.223.197.164',
            'role': 'vnf',
            'user': 'root',
            'password': 'r00t',
            'interfaces': {
                'xe0': {
                    'netmask': '255.255.255.0',
                    'local_ip': '152.16.100.19',
                    'local_mac': '00:00:00:00:00:03',
                    'driver': 'i40e',
                    'vpci': '0000:07:00.0',
                    'dpdk_port_num': 0,
                },
                'xe1': {
                    'netmask': '255.255.255.0',
                    'local_ip': '152.16.40.19',
                    'local_mac': '00:00:00:00:00:04',
                    'driver': 'i40e',
                    'vpci': '0000:07:00.1',
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
        }

        self.context_cfg = {
            'nodes': {
                'tg__1': self.tg__1,
                'vnf__1': self.vnf__1,
            },
            'networks': {
                GenericVNF.UPLINK: {
                    'vld_id': GenericVNF.UPLINK,
                },
                GenericVNF.DOWNLINK: {
                    'vld_id': GenericVNF.DOWNLINK,
                },
            },
        }

        self.vld0 = {
            'vnfd-connection-point-ref': [
                {
                    'vnfd-connection-point-ref': 'xe0',
                    'member-vnf-index-ref': '1',
                    'vnfd-id-ref': 'trexgen'
                },
                {
                    'vnfd-connection-point-ref': 'xe0',
                    'member-vnf-index-ref': '2',
                    'vnfd-id-ref': 'trexgen'
                }
            ],
            'type': 'ELAN',
            'id': GenericVNF.UPLINK,
            'name': 'tg__1 to vnf__1 link 1'
        }

        self.vld1 = {
            'vnfd-connection-point-ref': [
                {
                    'vnfd-connection-point-ref': 'xe1',
                    'member-vnf-index-ref': '1',
                    'vnfd-id-ref': 'trexgen'
                },
                {
                    'vnfd-connection-point-ref': 'xe1',
                    'member-vnf-index-ref': '2',
                    'vnfd-id-ref': 'trexgen'
                }
            ],
            'type': 'ELAN',
            'id': GenericVNF.DOWNLINK,
            'name': 'vnf__1 to tg__1 link 2'
        }

        self.topology = {
            'id': 'trex-tg-topology',
            'short-name': 'trex-tg-topology',
            'name': 'trex-tg-topology',
            'description': 'trex-tg-topology',
            'constituent-vnfd': [
                {
                    'member-vnf-index': '1',
                    'VNF model': 'tg_trex_tpl.yaml',
                    'vnfd-id-ref': 'tg__1',
                },
                {
                    'member-vnf-index': '2',
                    'VNF model': 'tg_trex_tpl.yaml',
                    'vnfd-id-ref': 'vnf__1',
                },
            ],
            'vld': [self.vld0, self.vld1],
        }

        self.scenario_cfg = {
            'task_path': "",
            "topology": self._get_file_abspath("vpe_vnf_topology.yaml"),
            'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
            'tc': 'tc_ipv4_1Mflow_64B_packetsize',
            'traffic_profile': 'ipv4_throughput_vpe.yaml',
            'extra_args': {'arg1': 'value1', 'arg2': 'value2'},
            'type': 'ISB',
            'tc_options': {
                'rfc2544': {
                    'allowed_drop_rate': '0.8 - 1',
                },
            },
            'options': {
                'framesize': {'64B': 100}
            },
            'runner': {
                'object': 'NetworkServiceTestCase',
                'interval': 35,
                'output_filename': 'yardstick.out',
                'runner_id': 74476,
                'duration': 400,
                'type': 'Duration',
            },
            'traffic_options': {
                'flow': 'ipv4_1flow_Packets_vpe.yaml',
                'imix': 'imix_voice.yaml'
            },
            'nodes': {
                'tg__2': 'trafficgen_2.yardstick',
                'tg__1': 'trafficgen_1.yardstick',
                'vnf__1': 'vnf.yardstick',
            },
        }

        self.s = vnf_generic.NetworkServiceTestCase(self.scenario_cfg,
                                                    self.context_cfg)

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test___init__(self):
        self.assertIsNotNone(self.topology)

    def test__get_ip_flow_range_string(self):
        self.scenario_cfg["traffic_options"]["flow"] = \
            self._get_file_abspath("ipv4_1flow_Packets_vpe.yaml")
        result = '152.16.100.2-152.16.100.254'
        self.assertEqual(result, self.s._get_ip_flow_range(
            '152.16.100.2-152.16.100.254'))

    def test__get_ip_flow_range(self):
        self.scenario_cfg["traffic_options"]["flow"] = \
            self._get_file_abspath("ipv4_1flow_Packets_vpe.yaml")
        result = '152.16.100.2-152.16.100.254'
        self.assertEqual(result, self.s._get_ip_flow_range({"tg__1": 'xe0'}))

    @mock.patch('yardstick.benchmark.scenarios.networking.vnf_generic.ipaddress')
    def test__get_ip_flow_range_no_node_data(self, mock_ipaddress):
        scenario_cfg = deepcopy(self.scenario_cfg)
        scenario_cfg["traffic_options"]["flow"] = \
            self._get_file_abspath("ipv4_1flow_Packets_vpe.yaml")

        mock_ipaddress.ip_network.return_value = ipaddr = mock.Mock()
        ipaddr.hosts.return_value = []

        expected = '0.0.0.0'
        result = self.s._get_ip_flow_range({"tg__2": 'xe0'})
        self.assertEqual(result, expected)

    def test__get_ip_flow_range_no_nodes(self):
        expected = '0.0.0.0'
        result = self.s._get_ip_flow_range({})
        self.assertEqual(result, expected)

    def test___get_traffic_flow(self):
        self.scenario_cfg["traffic_options"]["flow"] = \
            self._get_file_abspath("ipv4_1flow_Packets_vpe.yaml")
        self.scenario_cfg["options"] = {}
        self.scenario_cfg['options'] = {
            'flow': {
                'src_ip': [
                    {
                        'tg__1': 'xe0',
                    },
                ],
                'dst_ip': [
                    {
                        'tg__1': 'xe1',
                    },
                ],
                'public_ip': ['1.1.1.1'],
            },
        }
        # NOTE(ralonsoh): check the expected output. This test could be
        # incorrect
        # result = {'flow': {'dst_ip0': '152.16.40.2-152.16.40.254',
        #                    'src_ip0': '152.16.100.2-152.16.100.254'}}
        self.assertEqual({'flow': {}}, self.s._get_traffic_flow())

    def test___get_traffic_flow_error(self):
        self.scenario_cfg["traffic_options"]["flow"] = \
            "ipv4_1flow_Packets_vpe.yaml1"
        self.assertEqual({'flow': {}}, self.s._get_traffic_flow())

    def test_get_vnf_imp(self):
        vnfd = COMPLETE_TREX_VNFD['vnfd:vnfd-catalog']['vnfd'][0]['class-name']
        with mock.patch.dict(sys.modules, tests.STL_MOCKS):
            self.assertIsNotNone(self.s.get_vnf_impl(vnfd))

        with self.assertRaises(vnf_generic.IncorrectConfig) as raised:
            self.s.get_vnf_impl('NonExistentClass')

        exc_str = str(raised.exception)
        print(exc_str)
        self.assertIn('No implementation', exc_str)
        self.assertIn('found in', exc_str)

    def test_load_vnf_models_invalid(self):
        self.context_cfg["nodes"]['tg__1']['VNF model'] = \
            self._get_file_abspath("tg_trex_tpl.yaml")
        self.context_cfg["nodes"]['vnf__1']['VNF model'] = \
            self._get_file_abspath("tg_trex_tpl.yaml")

        vnf = mock.Mock(autospec=GenericVNF)
        self.s.get_vnf_impl = mock.Mock(return_value=vnf)

        self.assertIsNotNone(
            self.s.load_vnf_models(self.scenario_cfg, self.context_cfg))

    def test_load_vnf_models_no_model(self):
        vnf = mock.Mock(autospec=GenericVNF)
        self.s.get_vnf_impl = mock.Mock(return_value=vnf)

        self.assertIsNotNone(
            self.s.load_vnf_models(self.scenario_cfg, self.context_cfg))

    def test_map_topology_to_infrastructure(self):
        self.s.map_topology_to_infrastructure()

        nodes = self.context_cfg["nodes"]
        self.assertEqual('../../vnf_descriptors/tg_rfc2544_tpl.yaml',
                         nodes['tg__1']['VNF model'])
        self.assertEqual('../../vnf_descriptors/vpe_vnf.yaml',
                         nodes['vnf__1']['VNF model'])

    def test_map_topology_to_infrastructure_insufficient_nodes(self):
        cfg = deepcopy(self.context_cfg)
        del cfg['nodes']['vnf__1']

        cfg_patch = mock.patch.object(self.s, 'context_cfg', cfg)
        with cfg_patch:
            with self.assertRaises(IncorrectConfig):
                self.s.map_topology_to_infrastructure()

    def test_map_topology_to_infrastructure_config_invalid(self):
        ssh_mock = mock.Mock()
        ssh_mock.execute.return_value = 0, SYS_CLASS_NET + IP_ADDR_SHOW, ""

        cfg = deepcopy(self.s.context_cfg)

        # delete all, we don't know which will come first
        del cfg['nodes']['vnf__1']['interfaces']['xe0']['local_mac']
        del cfg['nodes']['vnf__1']['interfaces']['xe1']['local_mac']
        del cfg['nodes']['tg__1']['interfaces']['xe0']['local_mac']
        del cfg['nodes']['tg__1']['interfaces']['xe1']['local_mac']

        config_patch = mock.patch.object(self.s, 'context_cfg', cfg)
        with config_patch:
            with self.assertRaises(IncorrectConfig):
                self.s.map_topology_to_infrastructure()

    def test__resolve_topology_invalid_config(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock

            # purge an important key from the data structure
            for interface in self.tg__1['interfaces'].values():
                del interface['local_mac']

            with self.assertRaises(vnf_generic.IncorrectConfig) as raised:
                self.s._resolve_topology()

            self.assertIn('not found', str(raised.exception))

            # restore local_mac
            for index, interface in enumerate(self.tg__1['interfaces'].values()):
                interface['local_mac'] = '00:00:00:00:00:{:2x}'.format(index)

            # make a connection point ref with 3 points
            self.s.topology["vld"][0]['vnfd-connection-point-ref'].append(
                self.s.topology["vld"][0]['vnfd-connection-point-ref'][0])

            with self.assertRaises(vnf_generic.IncorrectConfig) as raised:
                self.s._resolve_topology()

            self.assertIn('wrong endpoint count', str(raised.exception))

            # make a connection point ref with 1 point
            self.s.topology["vld"][0]['vnfd-connection-point-ref'] = \
                self.s.topology["vld"][0]['vnfd-connection-point-ref'][:1]

            with self.assertRaises(vnf_generic.IncorrectConfig) as raised:
                self.s._resolve_topology()

            self.assertIn('wrong endpoint count', str(raised.exception))

    def test_run(self):
        tgen = mock.Mock(autospec=GenericTrafficGen)
        tgen.traffic_finished = True
        verified_dict = {"verified": True}
        tgen.verify_traffic = lambda x: verified_dict
        tgen.name = "tgen__1"
        vnf = mock.Mock(autospec=GenericVNF)
        vnf.runs_traffic = False
        self.s.vnfs = [tgen, vnf]
        self.s.traffic_profile = mock.Mock()
        self.s.collector = mock.Mock(autospec=Collector)
        self.s.collector.get_kpi = \
            mock.Mock(return_value={tgen.name: verified_dict})
        result = {}
        self.s.run(result)
        self.assertDictEqual(result, {tgen.name: verified_dict})

    def test_setup(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock

            tgen = mock.Mock(autospec=GenericTrafficGen)
            tgen.traffic_finished = True
            verified_dict = {"verified": True}
            tgen.verify_traffic = lambda x: verified_dict
            tgen.terminate = mock.Mock(return_value=True)
            tgen.name = "tgen__1"
            vnf = mock.Mock(autospec=GenericVNF)
            vnf.runs_traffic = False
            vnf.terminate = mock.Mock(return_value=True)
            self.s.vnfs = [tgen, vnf]
            self.s.traffic_profile = mock.Mock()
            self.s.collector = mock.Mock(autospec=Collector)
            self.s.collector.get_kpi = \
                mock.Mock(return_value={tgen.name: verified_dict})
            self.s.map_topology_to_infrastructure = mock.Mock(return_value=0)
            self.s.load_vnf_models = mock.Mock(return_value=self.s.vnfs)
            self.s._fill_traffic_profile = \
                mock.Mock(return_value=TRAFFIC_PROFILE)
            self.assertIsNone(self.s.setup())

    def test_setup_exception(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock

            tgen = mock.Mock(autospec=GenericTrafficGen)
            tgen.traffic_finished = True
            verified_dict = {"verified": True}
            tgen.verify_traffic = lambda x: verified_dict
            tgen.terminate = mock.Mock(return_value=True)
            tgen.name = "tgen__1"
            vnf = mock.Mock(autospec=GenericVNF)
            vnf.runs_traffic = False
            vnf.instantiate.side_effect = RuntimeError(
                "error during instantiate")
            vnf.terminate = mock.Mock(return_value=True)
            self.s.vnfs = [tgen, vnf]
            self.s.traffic_profile = mock.Mock()
            self.s.collector = mock.Mock(autospec=Collector)
            self.s.collector.get_kpi = \
                mock.Mock(return_value={tgen.name: verified_dict})
            self.s.map_topology_to_infrastructure = mock.Mock(return_value=0)
            self.s.load_vnf_models = mock.Mock(return_value=self.s.vnfs)
            self.s._fill_traffic_profile = \
                mock.Mock(return_value=TRAFFIC_PROFILE)
            with self.assertRaises(RuntimeError):
                self.s.setup()

    def test__get_traffic_profile(self):
        self.scenario_cfg["traffic_profile"] = \
            self._get_file_abspath("ipv4_throughput_vpe.yaml")
        self.assertIsNotNone(self.s._get_traffic_profile())

    def test__get_traffic_profile_exception(self):
        with mock.patch.dict(self.scenario_cfg, {'traffic_profile': ''}):
            with self.assertRaises(IOError):
                self.s._get_traffic_profile()

    def test___get_traffic_imix_exception(self):
        with mock.patch.dict(self.scenario_cfg["traffic_options"], {'imix': ''}):
            self.assertEqual({'imix': {'64B': 100}},
                             self.s._get_traffic_imix())

    @mock.patch.object(base.TrafficProfile, 'get')
    @mock.patch.object(vnfdgen, 'generate_vnfd')
    def test__fill_traffic_profile(self, mock_generate, mock_tprofile_get):
        fake_tprofile = mock.Mock()
        fake_vnfd = mock.Mock()
        with mock.patch.object(self.s, '_get_traffic_profile',
                               return_value=fake_tprofile) as mock_get_tp:
            mock_generate.return_value = fake_vnfd
            self.s._fill_traffic_profile()
            mock_get_tp.assert_called_once()
            mock_generate.assert_called_once_with(
                fake_tprofile,
                {'downlink': {},
                 'extra_args': {'arg1': 'value1', 'arg2': 'value2'},
                 'flow': {'flow': {}},
                 'imix': {'imix': {'64B': 100}},
                 'uplink': {}}
            )
            mock_tprofile_get.assert_called_once_with(fake_vnfd)

    @mock.patch.object(utils, 'open_relative_file')
    def test__get_topology(self, mock_open_path):
        self.s.scenario_cfg['topology'] = 'fake_topology'
        self.s.scenario_cfg['task_path'] = 'fake_path'
        mock_open_path.side_effect = mock.mock_open(read_data='fake_data')
        self.assertEqual('fake_data', self.s._get_topology())
        mock_open_path.assert_called_once_with('fake_topology', 'fake_path')

    @mock.patch.object(vnfdgen, 'generate_vnfd')
    def test__render_topology(self, mock_generate):
        fake_topology = 'fake_topology'
        mock_generate.return_value = {'nsd:nsd-catalog': {'nsd': ['fake_nsd']}}
        with mock.patch.object(self.s, '_get_topology',
                               return_value=fake_topology) as mock_get_topology:
            self.s._render_topology()
            mock_get_topology.assert_called_once()

        mock_generate.assert_called_once_with(
            fake_topology,
            {'extra_args': {'arg1': 'value1', 'arg2': 'value2'}}
        )
        self.assertEqual(self.s.topology, 'fake_nsd')

    def test_teardown(self):
        vnf = mock.Mock(autospec=GenericVNF)
        vnf.terminate = mock.Mock(return_value=True)
        vnf.name = str(vnf)
        self.s.vnfs = [vnf]
        self.s.traffic_profile = mock.Mock()
        self.s.collector = mock.Mock(autospec=Collector)
        self.s.collector.stop = \
            mock.Mock(return_value=True)
        self.assertIsNone(self.s.teardown())

    def test_teardown_exception(self):
        vnf = mock.Mock(autospec=GenericVNF)
        vnf.terminate = mock.Mock(
            side_effect=RuntimeError("error duing terminate"))
        vnf.name = str(vnf)
        self.s.vnfs = [vnf]
        self.s.traffic_profile = mock.Mock()
        self.s.collector = mock.Mock(autospec=Collector)
        self.s.collector.stop = \
            mock.Mock(return_value=True)
        with self.assertRaises(RuntimeError):
            self.s.teardown()
