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
import errno
import unittest
import mock

from yardstick.benchmark.scenarios.networking.vnf_generic import \
    SshManager, NetworkServiceTestCase, IncorrectConfig, \
    IncorrectSetup, open_relative_file
from yardstick.network_services.collector.subscriber import Collector
from yardstick.network_services.vnf_generic.vnf.base import \
    GenericTrafficGen, GenericVNF

STL_MOCKS = {
    'stl': mock.MagicMock(),
    'stl.trex_stl_lib': mock.MagicMock(),
    'stl.trex_stl_lib.base64': mock.MagicMock(),
    'stl.trex_stl_lib.binascii': mock.MagicMock(),
    'stl.trex_stl_lib.collections': mock.MagicMock(),
    'stl.trex_stl_lib.copy': mock.MagicMock(),
    'stl.trex_stl_lib.datetime': mock.MagicMock(),
    'stl.trex_stl_lib.functools': mock.MagicMock(),
    'stl.trex_stl_lib.imp': mock.MagicMock(),
    'stl.trex_stl_lib.inspect': mock.MagicMock(),
    'stl.trex_stl_lib.json': mock.MagicMock(),
    'stl.trex_stl_lib.linecache': mock.MagicMock(),
    'stl.trex_stl_lib.math': mock.MagicMock(),
    'stl.trex_stl_lib.os': mock.MagicMock(),
    'stl.trex_stl_lib.platform': mock.MagicMock(),
    'stl.trex_stl_lib.pprint': mock.MagicMock(),
    'stl.trex_stl_lib.random': mock.MagicMock(),
    'stl.trex_stl_lib.re': mock.MagicMock(),
    'stl.trex_stl_lib.scapy': mock.MagicMock(),
    'stl.trex_stl_lib.socket': mock.MagicMock(),
    'stl.trex_stl_lib.string': mock.MagicMock(),
    'stl.trex_stl_lib.struct': mock.MagicMock(),
    'stl.trex_stl_lib.sys': mock.MagicMock(),
    'stl.trex_stl_lib.threading': mock.MagicMock(),
    'stl.trex_stl_lib.time': mock.MagicMock(),
    'stl.trex_stl_lib.traceback': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_async_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_exceptions': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_ext': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_jsonrpc_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_interface': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_scapy': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_port': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_stats': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_streams': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_types': mock.MagicMock(),
    'stl.trex_stl_lib.types': mock.MagicMock(),
    'stl.trex_stl_lib.utils': mock.MagicMock(),
    'stl.trex_stl_lib.utils.argparse': mock.MagicMock(),
    'stl.trex_stl_lib.utils.collections': mock.MagicMock(),
    'stl.trex_stl_lib.utils.common': mock.MagicMock(),
    'stl.trex_stl_lib.utils.json': mock.MagicMock(),
    'stl.trex_stl_lib.utils.os': mock.MagicMock(),
    'stl.trex_stl_lib.utils.parsing_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.pwd': mock.MagicMock(),
    'stl.trex_stl_lib.utils.random': mock.MagicMock(),
    'stl.trex_stl_lib.utils.re': mock.MagicMock(),
    'stl.trex_stl_lib.utils.string': mock.MagicMock(),
    'stl.trex_stl_lib.utils.sys': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_tables': mock.MagicMock(),
    'stl.trex_stl_lib.utils.texttable': mock.MagicMock(),
    'stl.trex_stl_lib.warnings': mock.MagicMock(),
    'stl.trex_stl_lib.yaml': mock.MagicMock(),
    'stl.trex_stl_lib.zlib': mock.MagicMock(),
    'stl.trex_stl_lib.zmq': mock.MagicMock(),
}

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
                             'password': 'r00t'}},
             "networks": {},
             }

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
            'task_path': "",
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

        self.assertIsNotNone(
            self.s.load_vnf_models(self.scenario_cfg, self.context_cfg))

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

    SAMPLE_NETDEVS = {
            'enp11s0': {
                'address': '0a:de:ad:be:ef:f5',
                'device': '0x1533',
                'driver': 'igb',
                'ifindex': '2',
                'interface_name': 'enp11s0',
                'operstate': 'down',
                'pci_bus_id': '0000:0b:00.0',
                'subsystem_device': '0x1533',
                'subsystem_vendor': '0x15d9',
                'vendor': '0x8086'
                },
            'lan': {
                'address': '0a:de:ad:be:ef:f4',
                'device': '0x153a',
                'driver': 'e1000e',
                'ifindex': '3',
                'interface_name': 'lan',
                'operstate': 'up',
                'pci_bus_id': '0000:00:19.0',
                'subsystem_device': '0x153a',
                'subsystem_vendor': '0x15d9',
                'vendor': '0x8086'
                }
        }
    SAMPLE_VM_NETDEVS = {
        'eth1': {
            'address': 'fa:de:ad:be:ef:5b',
            'device': '0x0001',
            'driver': 'virtio_net',
            'ifindex': '3',
            'interface_name': 'eth1',
            'operstate': 'down',
            'pci_bus_id': '0000:00:04.0',
            'vendor': '0x1af4'
        }
    }

    def test_parse_netdev_info(self):
        output = """\
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/ifindex:2
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/address:0a:de:ad:be:ef:f5
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/operstate:down
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/vendor:0x8086
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/device:0x1533
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/subsystem_vendor:0x15d9
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/device/subsystem_device:0x1533
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/driver:igb
/sys/devices/pci0000:00/0000:00:1c.3/0000:0b:00.0/net/enp11s0/pci_bus_id:0000:0b:00.0
/sys/devices/pci0000:00/0000:00:19.0/net/lan/ifindex:3
/sys/devices/pci0000:00/0000:00:19.0/net/lan/address:0a:de:ad:be:ef:f4
/sys/devices/pci0000:00/0000:00:19.0/net/lan/operstate:up
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/vendor:0x8086
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/device:0x153a
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/subsystem_vendor:0x15d9
/sys/devices/pci0000:00/0000:00:19.0/net/lan/device/subsystem_device:0x153a
/sys/devices/pci0000:00/0000:00:19.0/net/lan/driver:e1000e
/sys/devices/pci0000:00/0000:00:19.0/net/lan/pci_bus_id:0000:00:19.0
"""
        res = NetworkServiceTestCase.parse_netdev_info(output)
        assert res == self.SAMPLE_NETDEVS

    def test_parse_netdev_info_virtio(self):
        output = """\
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/ifindex:3
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/address:fa:de:ad:be:ef:5b
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/operstate:down
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/device/vendor:0x1af4
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/device/device:0x0001
/sys/devices/pci0000:00/0000:00:04.0/virtio1/net/eth1/driver:virtio_net
"""
        res = NetworkServiceTestCase.parse_netdev_info(output)
        assert res == self.SAMPLE_VM_NETDEVS

    def test_sort_dpdk_port_num(self):
        netdevs = self.SAMPLE_NETDEVS.copy()
        NetworkServiceTestCase._sort_dpdk_port_num(netdevs)
        assert netdevs['lan']['dpdk_port_num'] == 1
        assert netdevs['enp11s0']['dpdk_port_num'] == 2

    def test_probe_missing_values(self):
        netdevs = self.SAMPLE_NETDEVS.copy()
        NetworkServiceTestCase._sort_dpdk_port_num(netdevs)
        network = {'local_mac': '0a:de:ad:be:ef:f5'}
        NetworkServiceTestCase._probe_missing_values(netdevs, network, set())
        assert network['dpdk_port_num'] == 2

        network = {'local_mac': '0a:de:ad:be:ef:f4'}
        NetworkServiceTestCase._probe_missing_values(netdevs, network, set())
        assert network['dpdk_port_num'] == 1

    def test_open_relative_path(self):
        mock_open = mock.mock_open()
        mock_open_result = mock_open()
        mock_open_call_count = 1  # initial call to get result

        module_name = \
            'yardstick.benchmark.scenarios.networking.vnf_generic.open'

        # test
        with mock.patch(module_name, mock_open, create=True):
            self.assertEqual(open_relative_file('foo', 'bar'), mock_open_result)

            mock_open_call_count += 1  # one more call expected
            self.assertEqual(mock_open.call_count, mock_open_call_count)
            self.assertIn('foo', mock_open.call_args_list[-1][0][0])
            self.assertNotIn('bar', mock_open.call_args_list[-1][0][0])

            def open_effect(*args, **kwargs):
                if kwargs.get('name', args[0]) == os.path.join('bar', 'foo'):
                    return mock_open_result
                raise IOError(errno.ENOENT, 'not found')

            mock_open.side_effect = open_effect
            self.assertEqual(open_relative_file('foo', 'bar'), mock_open_result)

            mock_open_call_count += 2  # two more calls expected
            self.assertEqual(mock_open.call_count, mock_open_call_count)
            self.assertIn('foo', mock_open.call_args_list[-1][0][0])
            self.assertIn('bar', mock_open.call_args_list[-1][0][0])

            # test an IOError of type ENOENT
            mock_open.side_effect = IOError(errno.ENOENT, 'not found')
            with self.assertRaises(IOError):
                # the second call still raises
                open_relative_file('foo', 'bar')

            mock_open_call_count += 2  # two more calls expected
            self.assertEqual(mock_open.call_count, mock_open_call_count)
            self.assertIn('foo', mock_open.call_args_list[-1][0][0])
            self.assertIn('bar', mock_open.call_args_list[-1][0][0])

            # test an IOError other than ENOENT
            mock_open.side_effect = IOError(errno.EBUSY, 'busy')
            with self.assertRaises(IOError):
                open_relative_file('foo', 'bar')

            mock_open_call_count += 1  # one more call expected
            self.assertEqual(mock_open.call_count, mock_open_call_count)
