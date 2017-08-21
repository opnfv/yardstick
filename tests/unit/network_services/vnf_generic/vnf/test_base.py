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
    QueueFileWrapper, GenericVNF, GenericTrafficGen

IP_PIPELINE_CFG_FILE_TPL = """
arp_route_tbl = ({port0_local_ip_hex},{port0_netmask_hex},1,"""
"""{port1_local_ip_hex}) ({port1_local_ip_hex},{port1_netmask_hex},0,"""
"""{port0_local_ip_hex})"""

IP_PIPELINE_ND_CFG_FILE_TPL = """
nd_route_tbl = ({port1_dst_ip_hex6},"""
"""{port1_dst_netmask_hex6},1,{port1_dst_ip_hex6})"""

_LOCAL_OBJECT = object()


class FileAbsPath(object):
    def __init__(self, module_file):
        super(FileAbsPath, self).__init__()
        self.module_path = os.path.dirname(os.path.abspath(module_file))

    def get_path(self, filename):
        file_path = os.path.join(self.module_path, filename)
        return file_path


def mock_ssh(ssh, spec=None, exec_result=_LOCAL_OBJECT, run_result=_LOCAL_OBJECT):
    if spec is None:
        spec = ssh.SSH

    if exec_result is _LOCAL_OBJECT:
        exec_result = 0, "", ""

    if run_result is _LOCAL_OBJECT:
        run_result = 0, "", ""

    ssh_mock = mock.Mock(autospec=spec)
    ssh_mock._get_client.return_value = mock.Mock()
    ssh_mock.execute.return_value = exec_result
    ssh_mock.run.return_value = run_result
    ssh.from_node.return_value = ssh_mock


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


class TestGenericVNF(unittest.TestCase):

    VNFD_0 = {
        'short-name': 'VpeVnf',
        'vdu': [
            {
                'routing_table': [
                    {
                        'network': '152.16.100.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'if': 'xe0'
                    },
                    {
                        'network': '152.16.40.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'if': 'xe1'
                    },
                ],
                'description': 'VPE approximation using DPDK',
                'name': 'vpevnf-baremetal',
                'nd_route_tbl': [
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0'
                    },
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1'
                    },
                ],
                'id': 'vpevnf-baremetal',
                'external-interface': [
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:03',
                            'vpci': '0000:05:00.0',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': '0',
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.20',
                            'local_mac': '00:00:00:00:00:01'
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0'
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.1',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': '1',
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_mac': '00:00:00:00:00:02'
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1'
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
            'ip': '1.1.1.1'
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
        'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ]
        }
    }

    def test___init__(self):
        generic_vnf = GenericVNF('vnf1', self.VNFD_0)
        assert generic_vnf.kpi

    def test_collect_kpi(self):
        generic_vnf = GenericVNF('vnf1', self.VNFD_0)
        self.assertRaises(NotImplementedError, generic_vnf.collect_kpi)

    def test__get_kpi_definition(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_vnf = GenericVNF('vnf1', vnfd)
        kpi = generic_vnf._get_kpi_definition()
        self.assertEqual(kpi, ['packets_in', 'packets_fwd', 'packets_dropped'])

    def test_instantiate(self):
        generic_vnf = GenericVNF('vnf1', self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        with self.assertRaises(NotImplementedError):
            generic_vnf.instantiate({}, {})

    def test_scale(self):
        generic_vnf = GenericVNF('vnf1', self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        with self.assertRaises(NotImplementedError):
            generic_vnf.scale()

    def test_terminate(self):
        generic_vnf = GenericVNF('vnf1', self.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        with self.assertRaises(NotImplementedError):
            generic_vnf.terminate()


class TestGenericTrafficGen(unittest.TestCase):
    def test___init__(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = GenericTrafficGen('vnf1', vnfd)
        assert generic_traffic_gen.name == "vnf1"

    def test_listen_traffic(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = GenericTrafficGen('vnf1', vnfd)
        traffic_profile = {}
        self.assertIsNone(generic_traffic_gen.listen_traffic(traffic_profile))

    def test_run_traffic(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = GenericTrafficGen('vnf1', vnfd)
        traffic_profile = {}
        self.assertRaises(NotImplementedError,
                          generic_traffic_gen.run_traffic, traffic_profile)

    def test_terminate(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = GenericTrafficGen('vnf1', vnfd)
        self.assertRaises(NotImplementedError, generic_traffic_gen.terminate)

    def test_verify_traffic(self):
        vnfd = TestGenericVNF.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        generic_traffic_gen = GenericTrafficGen('vnf1', vnfd)
        traffic_profile = {}
        self.assertIsNone(generic_traffic_gen.verify_traffic(traffic_profile))
