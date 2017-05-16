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

# Unittest for yardstick.benchmark.scenarios.networking.test_vnf_generic

from __future__ import absolute_import
import os
import unittest
import mock

from tests.unit import STL_MOCKS
from yardstick.benchmark.scenarios.networking.vnf_generic import \
    SshManager, NetworkServiceTestCase, IncorrectConfig, IncorrectSetup
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.vnf_generic.vnf.base import \
    GenericTrafficGen, GenericVNF


COMPLETE_TREX_VNFD = \
    {'vnfd:vnfd-catalog':
     {'vnfd':
      [{'benchmark':
        {'kpi':
         ['rx_throughput_fps',
          'tx_throughput_fps',
          'tx_throughput_mbps',
          'rx_throughput_mbps',
          'tx_throughput_pc_linerate',
          'rx_throughput_pc_linerate',
          'min_latency',
          'max_latency',
          'avg_latency']},
        'connection-point': [{'name': 'xe0',
                              'type': 'VPORT'},
                             {'name': 'xe1',
                              'type': 'VPORT'}],
        'description': 'TRex stateless traffic generator for RFC2544',
        'id': 'TrexTrafficGen',
        'mgmt-interface': {'ip': '1.1.1.1',
                           'password': 'berta',
                           'user': 'berta',
                           'vdu-id': 'trexgen-baremetal'},
        'name': 'trexgen',
        'short-name': 'trexgen',
        'vdu': [{'description': 'TRex stateless traffic generator for RFC2544',
                 'external-interface':
                 [{'name': 'xe0',
                   'virtual-interface': {'bandwidth': '10 Gbps',
                                         'dst_ip': '1.1.1.1',
                                         'dst_mac': '00:01:02:03:04:05',
                                         'local_ip': '1.1.1.2',
                                         'local_mac': '00:01:02:03:05:05',
                                         'type': 'PCI-PASSTHROUGH',
                                         'netmask': "255.255.255.0",
                                         'driver': 'i40',
                                         'vpci': '0000:00:10.2'},
                   'vnfd-connection-point-ref': 'xe0'},
                  {'name': 'xe1',
                   'virtual-interface': {'bandwidth': '10 Gbps',
                                         'dst_ip': '2.1.1.1',
                                         'dst_mac': '00:01:02:03:04:06',
                                         'local_ip': '2.1.1.2',
                                         'local_mac': '00:01:02:03:05:06',
                                         'type': 'PCI-PASSTHROUGH',
                                         'netmask': "255.255.255.0",
                                         'driver': 'i40',
                                         'vpci': '0000:00:10.1'},
                   'vnfd-connection-point-ref': 'xe1'}],
                 'id': 'trexgen-baremetal',
                 'name': 'trexgen-baremetal'}]}]}}

IP_ADDR_SHOW = """
28: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP """
"""group default qlen 1000
    link/ether 90:e2:ba:a7:6a:c8 brd ff:ff:ff:ff:ff:ff
    inet 1.1.1.1/8 brd 1.255.255.255 scope global eth1
    inet6 fe80::92e2:baff:fea7:6ac8/64 scope link
       valid_lft forever preferred_lft forever
29: eth5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP """
"""group default qlen 1000
    link/ether 90:e2:ba:a7:6a:c9 brd ff:ff:ff:ff:ff:ff
    inet 2.1.1.1/8 brd 2.255.255.255 scope global eth5
    inet6 fe80::92e2:baff:fea7:6ac9/64 scope link tentative
       valid_lft forever preferred_lft forever
"""

SYS_CLASS_NET = """
lrwxrwxrwx 1 root root 0 sie 10 14:16 eth1 -> """
"""../../devices/pci0000:80/0000:80:02.2/0000:84:00.1/net/eth1
lrwxrwxrwx 1 root root 0 sie  3 10:37 eth2 -> """
"""../../devices/pci0000:00/0000:00:01.1/0000:84:00.2/net/eth5
"""

TRAFFIC_PROFILE = {
    "schema": "isb:traffic_profile:0.1",
    "name": "fixed",
    "description": "Fixed traffic profile to run UDP traffic",
    "traffic_profile": {
        "traffic_type": "FixedTraffic",
        "frame_rate": 100,  # pps
        "flow_number": 10,
        "frame_size": 64}}


class TestNetworkServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.context_cfg = \
            {'nodes':
             {'trexgen__1': {'role': 'TrafficGen',
                             'name': 'trafficgen_1.yardstick',
                             'ip': '10.10.10.11',
                             'interfaces':
                             {'xe0':
                              {'netmask': '255.255.255.0',
                               'local_ip': '152.16.100.20',
                               'local_mac': '00:00:00:00:00:01',
                               'driver': 'i40e',
                               'vpci': '0000:07:00.0',
                               'dpdk_port_num': 0},
                              'xe1':
                              {'netmask': '255.255.255.0',
                               'local_ip': '152.16.40.20',
                               'local_mac': '00:00:00:00:00:02',
                               'driver': 'i40e',
                               'vpci': '0000:07:00.1',
                               'dpdk_port_num': 1}},
                             'password': 'r00t',
                             'user': 'root'},
              'trexvnf__1': {'name': 'vnf.yardstick',
                             'ip': '10.10.10.12',
                             'interfaces':
                             {'xe0':
                              {'netmask': '255.255.255.0',
                               'local_ip': '152.16.100.19',
                               'local_mac': '00:00:00:00:00:03',
                               'driver': 'i40e',
                               'vpci': '0000:07:00.0',
                               'dpdk_port_num': 0},
                              'xe1': {'netmask': '255.255.255.0',
                                      'local_ip': '152.16.40.19',
                                      'local_mac': '00:00:00:00:00:04',
                                      'driver': 'i40e',
                                      'vpci': '0000:07:00.1',
                                      'dpdk_port_num': 1}},
                             'routing_table': [{'netmask': '255.255.255.0',
                                                'gateway': '152.16.100.20',
                                                'network': '152.16.100.20',
                                                'if': 'xe0'},
                                               {'netmask': '255.255.255.0',
                                                'gateway': '152.16.40.20',
                                                'network': '152.16.40.20',
                                                'if': 'xe1'}],
                             'host': '10.223.197.164',
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
                             'password': 'r00t'}}}

        self.topology = {
            'short-name': 'trex-tg-topology',
            'constituent-vnfd':
                [{'member-vnf-index': '1',
                  'VNF model': 'tg_trex_tpl.yaml',
                  'vnfd-id-ref': 'trexgen__1'},
                 {'member-vnf-index': '2',
                  'VNF model': 'tg_trex_tpl.yaml',
                  'vnfd-id-ref': 'trexvnf__1'}],
            'description': 'trex-tg-topology',
            'name': 'trex-tg-topology',
            'vld': [
                {
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
                    'id': 'private',
                    'name': 'trexgen__1 to trexvnf__1 link 1'
                },
                {
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
                    'id': 'public',
                    'name': 'trexvnf__1 to trexgen__1 link 2'
                }],
            'id': 'trex-tg-topology',
        }

        self.scenario_cfg = {
            'tc_options': {'rfc2544': {'allowed_drop_rate': '0.8 - 1'}},
            'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
            'tc': 'tc_ipv4_1Mflow_64B_packetsize',
            'runner': {'object': 'NetworkServiceTestCase',
                       'interval': 35,
                       'output_filename': 'yardstick.out',
                       'runner_id': 74476,
                       'duration': 400, 'type': 'Duration'},
            'traffic_profile': 'ipv4_throughput_vpe.yaml',
            'traffic_options': {'flow': 'ipv4_1flow_Packets_vpe.yaml',
                                'imix': 'imix_voice.yaml'}, 'type': 'ISB',
            'nodes': {'tg__2': 'trafficgen_2.yardstick',
                      'tg__1': 'trafficgen_1.yardstick',
                      'vnf__1': 'vnf.yardstick'},
            "topology": self._get_file_abspath("vpe_vnf_topology.yaml")}

        self.s = NetworkServiceTestCase(self.scenario_cfg, self.context_cfg)

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test_ssh_manager(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock
            for node, node_dict in self.context_cfg["nodes"].items():
                with SshManager(node_dict) as conn:
                    self.assertIsNotNone(conn)

    def test___init__(self):
        assert self.topology

    def test___get_traffic_flow(self):
        self.scenario_cfg["traffic_options"]["flow"] = \
            self._get_file_abspath("ipv4_1flow_Packets_vpe.yaml")
        result = {'flow': {'dstip4_range': '152.40.0.20',
                           'srcip4_range': '152.16.0.20', 'count': 1}}
        self.assertEqual(result, self.s._get_traffic_flow(self.scenario_cfg))

    def test___get_traffic_flow_error(self):
        self.scenario_cfg["traffic_options"]["flow"] = \
            "ipv4_1flow_Packets_vpe.yaml1"
        self.assertEqual({}, self.s._get_traffic_flow(self.scenario_cfg))

    def test_get_vnf_imp(self):
        vnfd = COMPLETE_TREX_VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        with mock.patch.dict("sys.modules", STL_MOCKS):
            self.assertIsNotNone(self.s.get_vnf_impl(vnfd))

    def test_load_vnf_models_invalid(self):
        self.context_cfg["nodes"]['trexgen__1']['VNF model'] = \
            self._get_file_abspath("tg_trex_tpl.yaml")
        self.context_cfg["nodes"]['trexvnf__1']['VNF model'] = \
            self._get_file_abspath("tg_trex_tpl.yaml")

        vnf = mock.Mock(autospec=GenericVNF)
        self.s.get_vnf_impl = mock.Mock(return_value=vnf)

        self.assertIsNotNone(self.s.load_vnf_models(self.context_cfg))

    def test_map_topology_to_infrastructure(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock
            self.s.map_topology_to_infrastructure(self.context_cfg,
                                                  self.topology)
        self.assertEqual("tg_trex_tpl.yaml",
                         self.context_cfg["nodes"]['trexgen__1']['VNF model'])
        self.assertEqual("tg_trex_tpl.yaml",
                         self.context_cfg["nodes"]['trexvnf__1']['VNF model'])

    def test_map_topology_to_infrastructure_insufficient_nodes(self):
        del self.context_cfg['nodes']['trexvnf__1']
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock

            self.assertRaises(IncorrectSetup,
                              self.s.map_topology_to_infrastructure,
                              self.context_cfg, self.topology)

    def test_map_topology_to_infrastructure_config_invalid(self):
        cfg = dict(self.context_cfg)
        del cfg['nodes']['trexvnf__1']['interfaces']['xe0']['local_mac']
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock

            self.assertRaises(IncorrectConfig,
                              self.s.map_topology_to_infrastructure,
                              self.context_cfg, self.topology)

    def test__resolve_topology_invalid_config(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, SYS_CLASS_NET + IP_ADDR_SHOW, ""))
            ssh.from_node.return_value = ssh_mock

            del self.context_cfg['nodes']
            self.assertRaises(IncorrectConfig, self.s._resolve_topology,
                              self.context_cfg, self.topology)

            self.topology['vld'][0]['vnfd-connection-point-ref'].append(
                self.topology['vld'][0]['vnfd-connection-point-ref'])
            self.assertRaises(IncorrectConfig, self.s._resolve_topology,
                              self.context_cfg, self.topology)

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
            self.assertEqual(None, self.s.setup())

    def test__get_traffic_profile(self):
        self.scenario_cfg["traffic_profile"] = \
            self._get_file_abspath("ipv4_throughput_vpe.yaml")
        self.assertIsNotNone(self.s._get_traffic_profile(self.scenario_cfg,
                                                         self.context_cfg))

    def test__get_traffic_profile_exception(self):
        cfg = dict(self.scenario_cfg)
        cfg["traffic_profile"] = ""
        self.assertRaises(IOError, self.s._get_traffic_profile, cfg,
                          self.context_cfg)

    def test___get_traffic_imix_exception(self):
        cfg = dict(self.scenario_cfg)
        cfg["traffic_options"]["imix"] = ""
        self.assertEqual({}, self.s._get_traffic_imix(cfg))

    def test__fill_traffic_profile(self):
        with mock.patch.dict("sys.modules", STL_MOCKS):
            self.scenario_cfg["traffic_profile"] = \
                self._get_file_abspath("ipv4_throughput_vpe.yaml")
            self.scenario_cfg["traffic_options"]["flow"] = \
                self._get_file_abspath("ipv4_1flow_Packets_vpe.yaml")
            self.scenario_cfg["traffic_options"]["imix"] = \
                self._get_file_abspath("imix_voice.yaml")
            self.assertIsNotNone(self.s._fill_traffic_profile(self.scenario_cfg,
                                                              self.context_cfg))

    def test_teardown(self):
        vnf = mock.Mock(autospec=GenericVNF)
        vnf.terminate = \
            mock.Mock(return_value=True)
        self.s.vnfs = [vnf]
        self.s.traffic_profile = mock.Mock()
        self.s.collector = mock.Mock(autospec=Collector)
        self.s.collector.stop = \
            mock.Mock(return_value=True)
        self.assertIsNone(self.s.teardown())
