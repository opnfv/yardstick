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

import copy

import mock
import unittest

from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh
from yardstick.tests import STL_MOCKS


SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'
NAME = 'vnf_1'

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.tg_trex import \
        TrexTrafficGen, TrexResourceHelper
    from yardstick.network_services.traffic_profile.base import TrafficProfile


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
                        "vld_id": TrafficProfile.UPLINK,
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
                        "vld_id": TrafficProfile.DOWNLINK,
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
                        "vld_id": TrafficProfile.DOWNLINK,
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
                        "vld_id": TrafficProfile.UPLINK,
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

    @mock.patch(SSH_HELPER)
    def test___init__(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        self.assertIsInstance(
            trex_traffic_gen.resource_helper, TrexResourceHelper)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper._queue.put({})
        result = trex_traffic_gen.collect_kpi()
        self.assertEqual({}, result)

    @mock.patch(SSH_HELPER)
    def test_listen_traffic(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        self.assertIsNone(trex_traffic_gen.listen_traffic({}))

    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen._tg_process = mock.MagicMock()
        trex_traffic_gen._tg_process.start = mock.Mock()
        trex_traffic_gen._tg_process.exitcode = 0
        trex_traffic_gen._tg_process._is_alive = mock.Mock(return_value=1)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()

        self.assertIsNone(trex_traffic_gen.instantiate(
            self.SCENARIO_CFG, self.CONTEXT_CFG))

    @mock.patch(SSH_HELPER)
    def test_instantiate_error(self, ssh):
        mock_ssh(ssh, exec_result=(1, "", ""))

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen._tg_process = mock.MagicMock()
        trex_traffic_gen._tg_process.start = mock.Mock()
        trex_traffic_gen._tg_process._is_alive = mock.Mock(return_value=0)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.setup_helper.setup_vnf_environment = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.instantiate(
            self.SCENARIO_CFG, self.CONTEXT_CFG))

    @mock.patch(SSH_HELPER)
    def test__start_server(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.scenario_helper.scenario_cfg = {}
        self.assertIsNone(trex_traffic_gen._start_server())

    @mock.patch(SSH_HELPER)
    def test__start_server_multiple_queues(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.scenario_helper.scenario_cfg = {
            "options": {NAME: {"queues_per_port": 2}}}
        self.assertIsNone(trex_traffic_gen._start_server())

    @mock.patch(SSH_HELPER)
    def test__traffic_runner(self, ssh):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.execute_traffic.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.sut = TrexTrafficGen(NAME, vnfd)
        self.sut.ssh_helper = mock.Mock()
        self.sut.ssh_helper.run = mock.Mock()
        self.sut._connect_client = mock.Mock(autospec=STLClient)
        self.sut._connect_client.get_stats = mock.Mock(return_value="0")
        self.sut.resource_helper.RUN_DURATION = 0
        self.sut.resource_helper.QUEUE_WAIT_TIME = 0
        # must generate cfg before we can run traffic so Trex port mapping is created
        self.sut.resource_helper.generate_cfg()
        self.sut._traffic_runner(mock_traffic_profile)

    @mock.patch(SSH_HELPER)
    def test__generate_trex_cfg(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.resource_helper.generate_cfg())

    @mock.patch(SSH_HELPER)
    def test_build_ports_reversed_pci_ordering(self, ssh):
        mock_ssh(ssh)
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
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.generate_cfg()
        trex_traffic_gen.resource_helper._build_ports()
        self.assertEqual(
            sorted(trex_traffic_gen.resource_helper.all_ports), [0, 1])
        # there is a gap in ordering
        self.assertEqual(dict(trex_traffic_gen.resource_helper.dpdk_to_trex_port_map),
                         {0: 0, 2: 1})

    @mock.patch(SSH_HELPER)
    def test_run_traffic(self, ssh):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.sut = TrexTrafficGen(NAME, vnfd)
        self.sut.ssh_helper = mock.Mock()
        self.sut.ssh_helper.run = mock.Mock()
        self.sut._traffic_runner = mock.Mock(return_value=0)
        self.sut.resource_helper.client_started.value = 1
        result = self.sut.run_traffic(mock_traffic_profile)
        self.sut._traffic_process.terminate()
        self.assertIsNotNone(result)

    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.terminate())

    @mock.patch(SSH_HELPER)
    def test__connect_client(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        client = mock.Mock(autospec=STLClient)
        client.connect = mock.Mock(return_value=0)
        self.assertIsNotNone(trex_traffic_gen.resource_helper._connect(client))
