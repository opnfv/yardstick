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

# Unittest for yardstick.network_services.vnf_generic.vnf.test_base

from __future__ import absolute_import
import unittest
import os
import mock
from multiprocessing import Queue

from yardstick.network_services.vnf_generic.vnf.base import \
    QueueFileWrapper, GenericVNF, GenericTrafficGen, HelperFunc

IP_PIPELINE_CFG_FILE_TPL = """
arp_route_tbl = ({port0_local_ip_hex},{port0_netmask_hex},1,"""
"""{port1_local_ip_hex}) ({port1_local_ip_hex},{port1_netmask_hex},0,"""
"""{port0_local_ip_hex})"""

IP_PIPELINE_ND_CFG_FILE_TPL = """
nd_route_tbl = ({port1_dst_ip_hex6},"""
"""{port1_dst_netmask_hex6},1,{port1_dst_ip_hex6})"""


class TestQueueFileWrapper(unittest.TestCase):
    def setUp(self):
        self.prompt = "pipeline>"
        self.q_in = Queue()
        self.q_out = Queue()

    def test___init__(self):
        queue_file_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        self.assertEqual(queue_file_wrapper.prompt, self.prompt)

    def test_clear(self):
        queue_file_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        queue_file_wrapper.bufsize = 5
        queue_file_wrapper.write("pipeline>")
        queue_file_wrapper.close()
        self.assertIsNone(queue_file_wrapper.clear())
        self.assertIsNotNone(queue_file_wrapper.q_out.empty())

    def test_close(self):
        queue_file_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        self.assertEqual(None, queue_file_wrapper.close())

    def test_read(self):
        queue_file_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        queue_file_wrapper.q_in.put("pipeline>")
        self.assertEqual("pipeline>", queue_file_wrapper.read(20))

    def test_write(self):
        queue_file_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        queue_file_wrapper.write("pipeline>")
        self.assertIsNotNone(queue_file_wrapper.q_out.empty())


class TestHelperFunc(unittest.TestCase):

    def test___init__(self):
        HelperFunc()

    def test_generate_port_pairs(self):
        helperfunc = HelperFunc()
        curr_path = os.path.dirname(os.path.abspath(__file__))
        sample_topo = "samples/vnf_samples/nsut/vpe/vpe_vnf_topology.yaml"
        topology_file = os.path.join(curr_path,
                                     "../../../../../%s" % sample_topo)
        self.assertEqual(helperfunc.generate_port_pairs(topology_file),
                         [[('xe0', 'xe1')], [('xe0', 'xe1')]])


class TestGenericVNF(unittest.TestCase):
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
                   {'dst_mac': '00:00:00:00:00:03',
                    'vpci': '0000:05:00.0',
                    'local_ip': '152.16.100.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '0',
                    'bandwidth': '10 Gbps',
                    'dst_ip': '152.16.100.20',
                    'local_mac': '00:00:00:00:00:01'},
                   'vnfd-connection-point-ref': 'xe0',
                   'name': 'xe0'},
                  {'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:04',
                    'vpci': '0000:05:00.1',
                    'local_ip': '152.16.40.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '1',
                    'bandwidth': '10 Gbps',
                    'dst_ip': '152.16.40.20',
                    'local_mac': '00:00:00:00:00:02'},
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
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'}]}}

    def test___init__(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        assert generic_vn_f.kpi

    def test_collect_kpi(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        self.assertRaises(NotImplementedError, generic_vn_f.collect_kpi)

    def test_get_ip_version(self):
        ip_addr = "152.16.1.1"
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        self.assertEqual(4, generic_vn_f.get_ip_version(ip_addr))

    @mock.patch('yardstick.network_services.vnf_generic.vnf.base.LOG')
    def test_get_ip_version_error(self, mock_LOG):
        ip_addr = "152.16.1.1.1"
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        self.assertRaises(ValueError, generic_vn_f.get_ip_version(ip_addr))

    def test_ip_to_hex(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        hex_ip = generic_vn_f._ip_to_hex("192.168.10.1")
        self.assertEqual("C0A80A01", hex_ip)

    def test__update_config_file(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        vnf_str = "link"
        mcpi = ["pkt_type=1"]
        ip_pipeline_cfg = 'pkt_type'
        cfg_file = \
            generic_vn_f._update_config_file(ip_pipeline_cfg,
                                             mcpi, vnf_str)
        self.assertEqual("pkt_type= 1\ne", cfg_file)
        ip_pipeline_cfg = '1'
        cfg_file = \
            generic_vn_f._update_config_file(ip_pipeline_cfg,
                                             mcpi, vnf_str)
        self.assertEqual("type = link\npkt_type= 1\n1", cfg_file)
        mcpi = ["pkt_type="]
        ip_pipeline_cfg = '1'
        cfg_file = \
            generic_vn_f._update_config_file(ip_pipeline_cfg,
                                             mcpi, vnf_str)
        self.assertEqual("\n1", cfg_file)

    def test_update_packet_type(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ip_pipeline_cfg = 'pkt_type = ipv4'
        hex_ip = generic_vn_f._update_packet_type(ip_pipeline_cfg,
                                                  {'pkt_type': '1'})
        self.assertEqual("pkt_type = 1", hex_ip)

    def test_update_traffic_type(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ip_pipeline_cfg = 'pkt_type = ipv4'
        traffic_options = {"vnf_type": 'ACL', 'traffic_type': 4}
        result = generic_vn_f._update_traffic_type(ip_pipeline_cfg,
                                                   traffic_options)
        self.assertEqual("pkt_type = ipv4", result)
        traffic_options = {"vnf_type": 'CGNAT', 'traffic_type': 6}
        result = generic_vn_f._update_traffic_type(ip_pipeline_cfg,
                                                   traffic_options)
        self.assertEqual("pkt_type = ipv6", result)
        traffic_options = {"vnf_type": 'CGNAT', 'traffic_type': 4}
        result = generic_vn_f._update_traffic_type(ip_pipeline_cfg,
                                                   traffic_options)
        self.assertEqual("pkt_type = ipv4", result)

    def test__update_fw_script_file(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        vnf_str = "link"
        mcpi = ["link 0 down"]
        ip_pipeline_cfg = 'link 0 down\n link 0 config 152.16.100.10 24\n link 0'
        'p\nlink 1 down\nlink 1 config 152.40.40.10 24\nlink 1 up\np 1 arpadd'
        '152.40.40.20 00:00:00:00:00:02\np 1 arpadd 0 152.16.100.20 00:00:00:00:00:01\n'
        result = generic_vn_f._update_fw_script_file(ip_pipeline_cfg,
                                                     mcpi, vnf_str)
        self.assertIsNotNone(result)

    def test__update_cgnat_script_file(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ip_pipeline_cfg = "pipelineconfig"
        mcpi = ["link 0 down"]
        vnf_str = ''
        arp_route = generic_vn_f._update_cgnat_script_file(ip_pipeline_cfg,
                                                           mcpi, vnf_str)
        expected = '\nlink 0 down\n'
        self.assertEqual(expected, arp_route)
        mcpi = ["link 1 down"]
        arp_route = generic_vn_f._update_cgnat_script_file(ip_pipeline_cfg,
                                                           mcpi, vnf_str)
        expected = 'pipelineconfig\nlink 1 down\n'
        self.assertEqual(expected, arp_route)


    def test_append_routes(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        arp_route = generic_vn_f._append_routes(IP_PIPELINE_CFG_FILE_TPL)
        expected = '\narp_route_tbl = (98106414,FFFFFF00,0,98106414)' \
                   ' (98102814,FFFFFF00,1,98102814)\n,'
        self.assertEqual(expected, arp_route)

    def test_append_nd_routes(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        nd_route = generic_vn_f._append_nd_routes(IP_PIPELINE_ND_CFG_FILE_TPL)
        expected = '\nnd_route_tbl = (0064:ff9b:0:0:0:0:9810:6414,112,0,' \
                   '0064:ff9b:0:0:0:0:9810:6414) '\
                   '(0064:ff9b:0:0:0:0:9810:2814,112,'\
                   '1,0064:ff9b:0:0:0:0:9810:2814)\n,'
        self.assertEqual(expected, nd_route)

    def test_get_port0localip6(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port0_v6 = generic_vn_f._get_port0localip6()
        expected = '0064:ff9b:0:0:0:0:9810:6414'
        self.assertEqual(expected, port0_v6)

    def test_get_port1localip6(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port1_v6 = generic_vn_f._get_port1localip6()
        expected = '0064:ff9b:0:0:0:0:9810:2814'
        self.assertEqual(expected, port1_v6)

    def test_get_port0prefixip6(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port0_v6 = generic_vn_f._get_port0prefixlen6()
        self.assertEqual('112', port0_v6)

    def test_get_port1prefixip6(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port1_v6 = generic_vn_f._get_port1prefixlen6()
        self.assertEqual('112', port1_v6)

    def test_get_port0gateway6(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port0_v6 = generic_vn_f._get_port0gateway6()
        self.assertEqual('0064:ff9b:0:0:0:0:9810:6414', port0_v6)

    def test_get_port1gateway6(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port1_v6 = generic_vn_f._get_port1gateway6()
        self.assertEqual('0064:ff9b:0:0:0:0:9810:2814', port1_v6)

    def test_get_dpdk_port_num(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        port_num = generic_vn_f._get_dpdk_port_num('xe0')
        self.assertEqual('0', port_num)

    def test__get_kpi_definition(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_vn_f = GenericVNF(vnfd)
        kpi = \
            generic_vn_f._get_kpi_definition(vnfd)
        self.assertEqual(kpi, ['packets_in', 'packets_fwd', 'packets_dropped'])

    def test_instantiate(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        self.assertRaises(NotImplementedError,
                          generic_vn_f.instantiate, {}, {})

    def test_scale(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        self.assertRaises(NotImplementedError, generic_vn_f.scale)

    def test_terminate(self):
        generic_vn_f = GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        self.assertRaises(NotImplementedError, generic_vn_f.terminate)

    def test_generate_port_pairs(self):
        generic_vn_f = \
            GenericVNF(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        generic_vn_f.helperfunc = mock.MagicMock()
        generic_vn_f.helperfunc.generate_port_pairs = \
            mock.Mock(return_value=[0, 1])
        self.assertIsNone(
            generic_vn_f.generate_port_pairs("vnf_topology.yaml"))


class TestGenericTrafficGen(unittest.TestCase):
    def test___init__(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = \
            GenericTrafficGen(vnfd)
        assert generic_traffic_gen.name == "tgen__1"

    def test_listen_traffic(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = \
            GenericTrafficGen(vnfd)
        traffic_profile = {}
        self.assertIsNone(generic_traffic_gen.listen_traffic(traffic_profile))

    def test_run_traffic(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = \
            GenericTrafficGen(vnfd)
        traffic_profile = {}
        self.assertRaises(NotImplementedError,
                          generic_traffic_gen.run_traffic, traffic_profile)

    def test_terminate(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = \
            GenericTrafficGen(vnfd)
        self.assertRaises(NotImplementedError, generic_traffic_gen.terminate)

    def test_verify_traffic(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = \
            GenericTrafficGen(vnfd)
        traffic_profile = {}
        self.assertIsNone(generic_traffic_gen.verify_traffic(traffic_profile))

    def test_generate_port_pairs(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = \
            GenericTrafficGen(vnfd)
        generic_traffic_gen.helperfunc = mock.MagicMock()
        generic_traffic_gen.helperfunc.generate_port_pairs = \
            mock.Mock(return_value=[0, 1])
        self.assertIsNone(
            generic_traffic_gen.generate_port_pairs("vnf_topology.yaml"))
