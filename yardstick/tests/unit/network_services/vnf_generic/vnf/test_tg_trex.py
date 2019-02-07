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

import copy

import mock
import unittest

from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.traffic_profile import rfc2544
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import tg_trex
from yardstick.benchmark.contexts import base as ctx_base


NAME = 'vnf__1'


class TestTrexTrafficGen(unittest.TestCase):

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
                                    'vld_id': 'downlink_0',
                                    'ifname': 'xe0',
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
                                    'vld_id': 'uplink_0',
                                    'ifname': 'xe1',
                                    'local_mac': '00:00:00:00:00:01'},
                                   'vnfd-connection-point-ref': 'xe1',
                                   'name': 'xe1'}]}],
               'description': 'Vpe approximation using DPDK',
               'mgmt-interface':
               {'vdu-id': 'vpevnf-baremetal',
                'host': '1.1.1.1',
                'password': 'r00t',
                            'user': 'root',
                            'ip': '1.1.1.1'},
               'benchmark':
               {'kpi': ['packets_in', 'packets_fwd',
                        'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'}]}}

    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64
        },
    }

    SCENARIO_CFG = {
        "options": {
            "packetsize": 64,
            "traffic_type": 4,
            "rfc2544": {
                "allowed_drop_rate": "0.8 - 1",
            },
            "vnf__1": {
                "rules": "acl_1rule.yaml",
                "vnf_config": {
                    "lb_config": "SW",
                    "lb_count": 1,
                    "worker_config": "1C/1T",
                    "worker_threads": 1,
                }
            }
        },
        "task_id": "a70bdf4a-8e67-47a3-9dc1-273c14506eb7",
        "tc": "tc_ipv4_1Mflow_64B_packetsize",
        "runner": {
            "object": "NetworkServiceTestCase",
            "interval": 35,
            "output_filename": "/tmp/yardstick.out",
            "runner_id": 74476, "duration": 400,
            "type": "Duration"
        },
        "traffic_profile": "ipv4_throughput_acl.yaml",
        "traffic_options": {
            "flow": "ipv4_Packets_acl.yaml",
            "imix": "imix_voice.yaml"
        },
        "type": "ISB",
        "nodes": {
            "tg__2": "trafficgen_2.yardstick",
            "tg__1": "trafficgen_1.yardstick",
            "vnf__1": "vnf.yardstick"
        },
        "topology": "udpreplay-tg-topology-baremetal.yaml"
    }

    CONTEXT_CFG = {
        "nodes": {
            "vnf__1": {
                "vnfd-id-ref": "vnf__1",
                "ip": "1.2.1.1",
                "interfaces": {
                    "xe0": {
                        "local_iface_name": "ens786f0",
                        "vld_id": tp_base.TrafficProfile.UPLINK,
                        "netmask": "255.255.255.0",
                        "vpci": "0000:05:00.0",
                        "local_ip": "152.16.100.19",
                        "driver": "i40e",
                        "dst_ip": "152.16.100.20",
                        "local_mac": "00:00:00:00:00:02",
                        "dst_mac": "00:00:00:00:00:04",
                        "dpdk_port_num": 0
                    },
                    "xe1": {
                        "local_iface_name": "ens786f1",
                        "vld_id": tp_base.TrafficProfile.DOWNLINK,
                        "netmask": "255.255.255.0",
                        "vpci": "0000:05:00.1",
                        "local_ip": "152.16.40.19",
                        "driver": "i40e",
                        "dst_ip": "152.16.40.20",
                        "local_mac": "00:00:00:00:00:01",
                        "dst_mac": "00:00:00:00:00:03",
                        "dpdk_port_num": 1
                    }
                },
                "host": "1.2.1.1",
                "user": "root",
                "nd_route_tbl": [
                    {
                        "netmask": "112",
                        "if": "xe0",
                        "gateway": "0064:ff9b:0:0:0:0:9810:6414",
                        "network": "0064:ff9b:0:0:0:0:9810:6414"
                    },
                    {
                        "netmask": "112",
                        "if": "xe1",
                        "gateway": "0064:ff9b:0:0:0:0:9810:2814",
                        "network": "0064:ff9b:0:0:0:0:9810:2814"
                    }
                ],
                "password": "r00t",
                "VNF model": "udp_replay.yaml",
                "name": "vnf.yardstick",
                "member-vnf-index": "2",
                "routing_table": [
                    {
                        "netmask": "255.255.255.0",
                        "if": "xe0",
                        "gateway": "152.16.100.20",
                        "network": "152.16.100.20"
                    },
                    {
                        "netmask": "255.255.255.0",
                        "if": "xe1",
                        "gateway": "152.16.40.20",
                        "network": "152.16.40.20"
                    }
                ],
                "role": "vnf"
            },
            "trafficgen_2.yardstick": {
                "member-vnf-index": "3",
                "role": "TrafficGen",
                "name": "trafficgen_2.yardstick",
                "vnfd-id-ref": "tg__2",
                "ip": "1.2.1.1",
                "interfaces": {
                    "xe0": {
                        "local_iface_name": "ens513f0",
                        "vld_id": tp_base.TrafficProfile.DOWNLINK,
                        "netmask": "255.255.255.0",
                        "vpci": "0000:02:00.0",
                        "local_ip": "152.16.40.20",
                        "driver": "ixgbe",
                        "dst_ip": "152.16.40.19",
                        "local_mac": "00:00:00:00:00:03",
                        "dst_mac": "00:00:00:00:00:01",
                        "dpdk_port_num": 0
                    },
                    "xe1": {
                        "local_iface_name": "ens513f1",
                        "netmask": "255.255.255.0",
                        "network": "202.16.100.0",
                        "local_ip": "202.16.100.20",
                        "driver": "ixgbe",
                        "local_mac": "00:1e:67:d0:60:5d",
                        "vpci": "0000:02:00.1",
                        "dpdk_port_num": 1
                    }
                },
                "password": "r00t",
                "VNF model": "l3fwd_vnf.yaml",
                "user": "root"
            },
            "trafficgen_1.yardstick": {
                "member-vnf-index": "1",
                "role": "TrafficGen",
                "name": "trafficgen_1.yardstick",
                "vnfd-id-ref": "tg__1",
                "ip": "1.2.1.1",
                "interfaces": {
                    "xe0": {
                        "local_iface_name": "ens785f0",
                        "vld_id": tp_base.TrafficProfile.UPLINK,
                        "netmask": "255.255.255.0",
                        "vpci": "0000:05:00.0",
                        "local_ip": "152.16.100.20",
                        "driver": "i40e",
                        "dst_ip": "152.16.100.19",
                        "local_mac": "00:00:00:00:00:04",
                        "dst_mac": "00:00:00:00:00:02",
                        "dpdk_port_num": 0
                    },
                    "xe1": {
                        "local_ip": "152.16.100.21",
                        "driver": "i40e",
                        "vpci": "0000:05:00.1",
                        "dpdk_port_num": 1,
                        "local_iface_name": "ens785f1",
                        "netmask": "255.255.255.0",
                        "local_mac": "00:00:00:00:00:01"
                    }
                },
                "password": "r00t",
                "VNF model": "tg_rfc2544_tpl.yaml",
                "user": "root"
            }
        }
    }

    def setUp(self):
        self._mock_ssh_helper = mock.patch.object(sample_vnf, 'VnfSshHelper')
        self.mock_ssh_helper = self._mock_ssh_helper.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_ssh_helper.stop()

    def test___init__(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        self.assertIsInstance(trex_traffic_gen.resource_helper,
                              tg_trex.TrexResourceHelper)

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    def test_collect_kpi(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.scenario_helper.scenario_cfg = {
            'nodes': {trex_traffic_gen.name: "mock"}
        }
        trex_traffic_gen.resource_helper._queue.put({})
        result = trex_traffic_gen.collect_kpi()
        expected = {
            'physical_node': 'mock_node',
            'collect_stats': {}
        }
        self.assertEqual(expected, result)

    def test_listen_traffic(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        self.assertIsNone(trex_traffic_gen.listen_traffic({}))

    @mock.patch.object(ctx_base.Context, 'get_context_from_server', return_value='fake_context')
    def test_instantiate(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen._tg_process = mock.MagicMock()
        trex_traffic_gen._tg_process.start = mock.Mock()
        trex_traffic_gen._tg_process.exitcode = 0
        trex_traffic_gen._tg_process._is_alive = mock.Mock(return_value=1)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.instantiate(self.SCENARIO_CFG,
                                                       self.CONTEXT_CFG))

    @mock.patch.object(ctx_base.Context, 'get_context_from_server', return_value='fake_context')
    def test_instantiate_error(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen._tg_process = mock.MagicMock()
        trex_traffic_gen._tg_process.start = mock.Mock()
        trex_traffic_gen._tg_process._is_alive = mock.Mock(return_value=0)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.instantiate(self.SCENARIO_CFG,
                                                       self.CONTEXT_CFG))

    def test__start_server(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.scenario_helper.scenario_cfg = {}
        self.assertIsNone(trex_traffic_gen._start_server())

    def test__start_server_multiple_queues(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.scenario_helper.scenario_cfg = {
            "options": {NAME: {"queues_per_port": 2}}}
        self.assertIsNone(trex_traffic_gen._start_server())

    def test__traffic_runner(self):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.execute_traffic.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.sut = tg_trex.TrexTrafficGen(NAME, vnfd)
        self.sut.ssh_helper = mock.Mock()
        self.sut.ssh_helper.run = mock.Mock()
        self.sut._connect_client = mock.Mock()
        self.sut._connect_client.get_stats = mock.Mock(return_value="0")
        self.sut.resource_helper.RUN_DURATION = 0
        self.sut.resource_helper.QUEUE_WAIT_TIME = 0
        # must generate cfg before we can run traffic so Trex port mapping is
        # created
        self.sut.resource_helper.generate_cfg()
        with mock.patch.object(self.sut.resource_helper, 'run_traffic'):
            self.sut._traffic_runner(mock_traffic_profile)

    def test__generate_trex_cfg(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.resource_helper.generate_cfg())

    def test_build_ports_reversed_pci_ordering(self):
        vnfd = copy.deepcopy(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        vnfd['vdu'][0]['external-interface'] = [
            {'virtual-interface':
             {'dst_mac': '00:00:00:00:00:04',
              'vpci': '0000:05:00.0',
              'local_ip': '152.16.100.19',
              'type': 'PCI-PASSTHROUGH',
              'netmask': '255.255.255.0',
              'dpdk_port_num': 2,
              'bandwidth': '10 Gbps',
              'driver': "i40e",
              'dst_ip': '152.16.100.20',
              'local_iface_name': 'xe0',
              'vld_id': 'downlink_0',
              'ifname': 'xe0',
              'local_mac': '00:00:00:00:00:02'},
             'vnfd-connection-point-ref': 'xe0',
             'name': 'xe0'},
            {'virtual-interface':
             {'dst_mac': '00:00:00:00:00:03',
              'vpci': '0000:04:00.0',
              'local_ip': '152.16.40.19',
              'type': 'PCI-PASSTHROUGH',
              'driver': "i40e",
              'netmask': '255.255.255.0',
              'dpdk_port_num': 0,
              'bandwidth': '10 Gbps',
              'dst_ip': '152.16.40.20',
              'local_iface_name': 'xe1',
              'vld_id': 'uplink_0',
              'ifname': 'xe1',
              'local_mac': '00:00:00:00:00:01'},
             'vnfd-connection-point-ref': 'xe1',
             'name': 'xe1'}]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.generate_cfg()
        trex_traffic_gen.resource_helper._build_ports()
        self.assertEqual(sorted(trex_traffic_gen.resource_helper.all_ports),
                         [0, 1])
        # there is a gap in ordering
        self.assertEqual(
            {0: 0, 2: 1},
            dict(trex_traffic_gen.resource_helper.dpdk_to_trex_port_map))

    def test_run_traffic(self):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.sut = tg_trex.TrexTrafficGen(NAME, vnfd)
        self.sut.ssh_helper = mock.Mock()
        self.sut.ssh_helper.run = mock.Mock()
        self.sut._traffic_runner = mock.Mock(return_value=0)
        self.sut.resource_helper.client_started.value = 1
        result = self.sut.run_traffic(mock_traffic_profile)
        self.sut._traffic_process.terminate()
        self.assertIsNotNone(result)

    def test_terminate(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.terminate())

    def test__connect_client(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = tg_trex.TrexTrafficGen(NAME, vnfd)
        client = mock.Mock()
        client.connect = mock.Mock(return_value=0)
        self.assertIsNotNone(trex_traffic_gen.resource_helper._connect(client))


class TrexResourceHelperTestCase(unittest.TestCase):

    def test__get_samples(self):
        mock_setup_helper = mock.Mock()
        trex_rh = tg_trex.TrexResourceHelper(mock_setup_helper)
        trex_rh.vnfd_helper.interfaces = [
            {'name': 'interface1'},
            {'name': 'interface2'}]
        stats = {
            10: {'rx_pps': 5, 'ipackets': 200},
            20: {'rx_pps': 10, 'ipackets': 300},
            'latency': {1: {'latency': 'latency_port_10_pg_id_1'},
                        2: {'latency': 'latency_port_10_pg_id_2'},
                        3: {'latency': 'latency_port_20_pg_id_3'},
                        4: {'latency': 'latency_port_20_pg_id_4'}}
        }
        port_pg_id = rfc2544.PortPgIDMap()
        port_pg_id.add_port(10)
        port_pg_id.increase_pg_id()
        port_pg_id.increase_pg_id()
        port_pg_id.add_port(20)
        port_pg_id.increase_pg_id()
        port_pg_id.increase_pg_id()

        with mock.patch.object(trex_rh, 'get_stats') as mock_get_stats, \
                mock.patch.object(trex_rh.vnfd_helper, 'port_num') as \
                mock_port_num:
            mock_get_stats.return_value = stats
            mock_port_num.side_effect = [10, 20]
            output = trex_rh._get_samples([10, 20], port_pg_id=port_pg_id)

        interface = output['interface1']
        self.assertEqual(5.0, interface['rx_throughput_fps'])
        self.assertEqual(200, interface['in_packets'])
        self.assertEqual('latency_port_10_pg_id_1', interface['latency'][1])
        self.assertEqual('latency_port_10_pg_id_2', interface['latency'][2])

        interface = output['interface2']
        self.assertEqual(10.0, interface['rx_throughput_fps'])
        self.assertEqual(300, interface['in_packets'])
        self.assertEqual('latency_port_20_pg_id_3', interface['latency'][3])
        self.assertEqual('latency_port_20_pg_id_4', interface['latency'][4])
