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

from tests.unit import STL_MOCKS
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.router_vnf import RouterVNF


TEST_FILE_YAML = 'nsb_test_case.yaml'
SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'


name = 'vnf__1'


class TestRouterVNF(unittest.TestCase):
    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
             [{'short-name': 'RouterVNF',
               'vdu':
               [{'routing_table': [],
                 'description': 'RouterVNF',
                 'name': 'router-baremetal',
                 'nd_route_tbl': [],
                 'id': 'router-baremetal',
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
                    'local_mac': '00:00:00:00:00:01'},
                   'vnfd-connection-point-ref': 'xe1',
                   'name': 'xe1'}]}],
               'description': 'RouterVNF',
               'mgmt-interface':
                   {'vdu-id': 'router-baremetal',
                    'host': '1.2.1.1',
                    'password': 'r00t',
                    'user': 'root',
                    'ip': '1.2.1.1'},
               'benchmark':
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'RouterVNF', 'name': 'VPEVnfSsh'}]}}

    scenario_cfg = {'nodes': {'cpt__0': 'compute_0.compute_nodes',
                              'tg__0': 'trafficgen_1.baremetal',
                              'vnf__0': 'vnf.yardstick'},
                    'options': {'flow': {'count': 128000,
                                         'dst_ip': ['10.0.3.26-10.0.3.105'],
                                         'dst_port': ['2001-2004'],
                                         'src_ip': ['10.0.2.26-10.0.2.105'],
                                         'src_port': ['1234-1238']},
                                'framesize': {'downlink': {'1024B': 100},
                                              'uplink': {'1024B': 100}},
                                'rfc2544': {'allowed_drop_rate': '0.0001 - 0.1'},
                                'tg__0': {'queues_per_port': 7},
                                'traffic_type': 4,
                                'vnf__0': {'nfvi_enable': True}},
                    'runner': {'interval': 35,
                               'iterations': 10,
                               'type': 'Iteration'},
                    'topology': 'router-tg-topology.yaml',
                    'traffic_profile': '../../traffic_profiles/ipv4_throughput.yaml',
                    'type': 'NSPerf'}

    context_cfg = {'nodes': {'tg__1':
                             {'member-vnf-index': '1',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_1.yardstick',
                              'vnfd-id-ref': 'tg__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens785f0',
                                       'vld_id': RouterVNF.UPLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.20',
                                       'dst_mac': '00:00:00:00:00:02',
                                       'local_mac': '00:00:00:00:00:04',
                                       'dst_ip': '152.16.100.19',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens785f1',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.21',
                                       'local_mac': '00:00:00:00:00:01',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'tg_rfc2544_tpl.yaml',
                              'user': 'root'},
                             'vnf__1':
                             {'name': 'vnf.yardstick',
                              'vnfd-id-ref': 'vnf__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens786f0',
                                       'vld_id': RouterVNF.UPLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.19',
                                       'dst_mac': '00:00:00:00:00:04',
                                       'local_mac': '00:00:00:00:00:02',
                                       'dst_ip': '152.16.100.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens786f1',
                                       'vld_id': RouterVNF.DOWNLINK,
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.19',
                                       'dst_mac': '00:00:00:00:00:03',
                                       'local_mac': '00:00:00:00:00:01',
                                       'dst_ip': '152.16.40.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'routing_table': [],
                              'member-vnf-index': '2',
                              'host': '1.2.1.1',
                              'role': 'vnf',
                              'user': 'root',
                              'nd_route_tbl': [],
                              'password': 'r00t',
                              'VNF model': 'router_vnf.yaml'}}}

    IP_SHOW_STATS_OUTPUT = """\
2: em1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
    link/ether d4:c9:ef:52:7c:4d brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped overrun mcast
    2781945429 3202213  0       0       0       30131
    RX errors: length  crc     frame   fifo    missed
               0        0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    646221183  2145799  0       0       0       0
    TX errors: aborted fifo    window  heartbeat
               0        0       0       0
"""
    STATS = {
        'RX:bytes': '2781945429',
        'RX:dropped': '0',
        'RX:errors': '0',
        'RX:mcast': '30131',
        'RX:overrun': '0',
        'RX:packets': '3202213',
        'RX errors:length': '0',
        'RX errors:crc': '0',
        'RX errors:frame': '0',
        'RX errors:fifo': '0',
        'RX errors:missed': '0',
        'TX:bytes': '646221183',
        'TX:carrier': '0',
        'TX:collsns': '0',
        'TX:dropped': '0',
        'TX:errors': '0',
        'TX:packets': '2145799',
        'TX errors:aborted': '0',
        'TX errors:fifo': '0',
        'TX errors:window': '0',
        'TX errors:heartbeat': '0',
    }

    def test___init__(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        router_vnf = RouterVNF(name, vnfd)
        self.assertIsNone(router_vnf._vnf_process)

    def test_get_stats(self):
        stats = RouterVNF.get_stats(self.IP_SHOW_STATS_OUTPUT)
        self.assertDictEqual(stats, self.STATS)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, _):
        m = mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        router_vnf = RouterVNF(name, vnfd)
        router_vnf.ssh_helper = m
        result = {'packets_dropped': 0, 'packets_fwd': 0, 'packets_in': 0, 'link_stats': {}}
        self.assertEqual(result, router_vnf.collect_kpi())

    @mock.patch(SSH_HELPER)
    def test_run_router(self, ssh):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        router_vnf = RouterVNF(name, vnfd)
        router_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
        router_vnf._run()
        router_vnf.ssh_helper.drop_connection.assert_called_once()

    @mock.patch("yardstick.network_services.vnf_generic.vnf.router_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, _):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        router_vnf = RouterVNF(name, vnfd)
        router_vnf.WAIT_TIME = 0
        router_vnf.INTERFACE_WAIT = 0
        self.scenario_cfg.update({"nodes": {"vnf__1": ""}})
        self.assertIsNone(router_vnf.instantiate(self.scenario_cfg,
                                                 self.context_cfg))

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, _):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        router_vnf = RouterVNF(name, vnfd)
        router_vnf._vnf_process = mock.MagicMock()
        router_vnf._vnf_process.terminate = mock.Mock()
        self.assertIsNone(router_vnf.terminate())
