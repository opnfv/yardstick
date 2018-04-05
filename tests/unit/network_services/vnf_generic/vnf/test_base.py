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

import multiprocessing
import os

import mock
import unittest

from yardstick.network_services.vnf_generic.vnf import base
from yardstick.ssh import SSH


IP_PIPELINE_CFG_FILE_TPL = ("arp_route_tbl = ({port0_local_ip_hex},"
                            "{port0_netmask_hex},1,{port1_local_ip_hex}) "
                            "({port1_local_ip_hex},{port1_netmask_hex},0,"
                            "{port0_local_ip_hex})")

IP_PIPELINE_ND_CFG_FILE_TPL = """
nd_route_tbl = ({port1_dst_ip_hex6},"""
"""{port1_dst_netmask_hex6},1,{port1_dst_ip_hex6})"""

_LOCAL_OBJECT = object()

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
                        'dpdk_port_num': 0,
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
                        'dpdk_port_num': 1,
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


class FileAbsPath(object):
    def __init__(self, module_file):
        super(FileAbsPath, self).__init__()
        self.module_path = os.path.dirname(os.path.abspath(module_file))

    def get_path(self, filename):
        file_path = os.path.join(self.module_path, filename)
        return file_path


def mock_ssh(mock_ssh_type, spec=None, exec_result=_LOCAL_OBJECT, run_result=_LOCAL_OBJECT):
    if spec is None:
        spec = SSH

    if exec_result is _LOCAL_OBJECT:
        exec_result = 0, "", ""

    if run_result is _LOCAL_OBJECT:
        run_result = 0, "", ""

    mock_ssh_instance = mock.Mock(autospec=spec)
    mock_ssh_instance._get_client.return_value = mock.Mock()
    mock_ssh_instance.execute.return_value = exec_result
    mock_ssh_instance.run.return_value = run_result
    mock_ssh_type.from_node.return_value = mock_ssh_instance
    return mock_ssh_instance


class TestQueueFileWrapper(unittest.TestCase):
    def setUp(self):
        self.prompt = "pipeline>"
        self.q_in = multiprocessing.Queue()
        self.q_out = multiprocessing.Queue()

    def test___init__(self):
        queue_file_wrapper = \
            base.QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        self.assertEqual(queue_file_wrapper.prompt, self.prompt)

    def test_clear(self):
        queue_file_wrapper = \
            base.QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        queue_file_wrapper.bufsize = 5
        queue_file_wrapper.write("pipeline>")
        queue_file_wrapper.close()
        self.assertIsNone(queue_file_wrapper.clear())
        self.assertIsNotNone(queue_file_wrapper.q_out.empty())

    def test_close(self):
        queue_file_wrapper = \
            base.QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        self.assertIsNone(queue_file_wrapper.close())

    def test_read(self):
        queue_file_wrapper = \
            base.QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        queue_file_wrapper.q_in.put("pipeline>")
        self.assertEqual("pipeline>", queue_file_wrapper.read(20))

    def test_write(self):
        queue_file_wrapper = \
            base.QueueFileWrapper(self.q_in, self.q_out, self.prompt)
        queue_file_wrapper.write("pipeline>")
        self.assertIsNotNone(queue_file_wrapper.q_out.empty())


class TestGenericVNF(unittest.TestCase):

    def test_definition(self):
        """Make sure that the abstract class cannot be instantiated"""
        with self.assertRaises(TypeError) as exc:
            # pylint: disable=abstract-class-instantiated
            base.GenericVNF('vnf1', VNFD['vnfd:vnfd-catalog']['vnfd'][0])

        msg = ("Can't instantiate abstract class GenericVNF with abstract methods "
               "collect_kpi, instantiate, scale, start_collect, "
               "stop_collect, terminate, wait_for_instantiate")

        self.assertEqual(msg, str(exc.exception))


class TestGenericTrafficGen(unittest.TestCase):

    def test_definition(self):
        """Make sure that the abstract class cannot be instantiated"""
        vnfd = VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        name = 'vnf1'
        with self.assertRaises(TypeError) as exc:
            # pylint: disable=abstract-class-instantiated
            base.GenericTrafficGen(name, vnfd)
        msg = ("Can't instantiate abstract class GenericTrafficGen with "
               "abstract methods collect_kpi, instantiate, run_traffic, "
               "scale, terminate")
        self.assertEqual(msg, str(exc.exception))
