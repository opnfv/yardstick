#!/usr/bin/env python

# Copyright (c) 2017 Intel Corporation
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

# Unittest for yardstick.network_services.vnf_generic.vnf.sample_vnf

from __future__ import absolute_import
import unittest
import mock

from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.ssh import SSHError

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

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import VnfSshHelper
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import DpdkVnfSetupEnvHelper


class TestVnfSshHelper(unittest.TestCase):

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

    def assertAll(self, iterable, message=None):
        self.assertTrue(all(iterable), message)

    def test_get_class(self):
        self.assertIs(VnfSshHelper.get_class(), VnfSshHelper)

    @mock.patch('yardstick.ssh.paramiko')
    def test_copy(self, _):
        ssh_helper = VnfSshHelper(self.VNFD_0['mgmt-interface'], 'my/bin/path')
        ssh_helper._run = mock.Mock()

        ssh_helper.execute('ls')
        self.assertTrue(ssh_helper.is_connected)
        result = ssh_helper.copy()
        self.assertIsInstance(result, VnfSshHelper)
        self.assertFalse(result.is_connected)
        self.assertEqual(result.bin_path, ssh_helper.bin_path)
        self.assertEqual(result.host, ssh_helper.host)
        self.assertEqual(result.port, ssh_helper.port)
        self.assertEqual(result.user, ssh_helper.user)
        self.assertEqual(result.password, ssh_helper.password)
        self.assertEqual(result.key_filename, ssh_helper.key_filename)

    @mock.patch('yardstick.ssh.paramiko')
    def test_upload_config_file(self, mock_paramiko):
        ssh_helper = VnfSshHelper(self.VNFD_0['mgmt-interface'], 'my/bin/path')

        self.assertFalse(ssh_helper.is_connected)
        cfg_file = ssh_helper.upload_config_file('my/prefix', 'my content')
        self.assertTrue(ssh_helper.is_connected)
        self.assertEqual(mock_paramiko.SSHClient.call_count, 1)
        self.assertTrue(cfg_file.startswith('/tmp'))

        cfg_file = ssh_helper.upload_config_file('/my/prefix', 'my content')
        self.assertTrue(ssh_helper.is_connected)
        self.assertEqual(mock_paramiko.SSHClient.call_count, 1)
        self.assertEqual(cfg_file, '/my/prefix')

    def test_join_bin_path(self):
        ssh_helper = VnfSshHelper(self.VNFD_0['mgmt-interface'], 'my/bin/path')

        expected_start = 'my'
        expected_middle_list = ['bin']
        expected_end = 'path'
        result = ssh_helper.join_bin_path()
        self.assertTrue(result.startswith(expected_start))
        self.assertAll(middle in result for middle in expected_middle_list)
        self.assertTrue(result.endswith(expected_end))

        expected_middle_list.append(expected_end)
        expected_end = 'some_file.sh'
        result = ssh_helper.join_bin_path('some_file.sh')
        self.assertTrue(result.startswith(expected_start))
        self.assertAll(middle in result for middle in expected_middle_list)
        self.assertTrue(result.endswith(expected_end))

        expected_middle_list.append('some_dir')
        expected_end = 'some_file.sh'
        result = ssh_helper.join_bin_path('some_dir', 'some_file.sh')
        self.assertTrue(result.startswith(expected_start))
        self.assertAll(middle in result for middle in expected_middle_list)
        self.assertTrue(result.endswith(expected_end))

    @mock.patch('yardstick.ssh.paramiko')
    @mock.patch('yardstick.ssh.provision_tool')
    def test_provision_tool(self, mock_provision_tool, mock_paramiko):
        ssh_helper = VnfSshHelper(self.VNFD_0['mgmt-interface'], 'my/bin/path')

        self.assertFalse(ssh_helper.is_connected)
        ssh_helper.provision_tool()
        self.assertTrue(ssh_helper.is_connected)
        self.assertEqual(mock_paramiko.SSHClient.call_count, 1)
        self.assertEqual(mock_provision_tool.call_count, 1)

        ssh_helper.provision_tool(tool_file='my_tool.sh')
        self.assertTrue(ssh_helper.is_connected)
        self.assertEqual(mock_paramiko.SSHClient.call_count, 1)
        self.assertEqual(mock_provision_tool.call_count, 2)


class TestSetupEnvHelper(unittest.TestCase):

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

    def test_build_config(self):
        setup_env_helper = SetupEnvHelper(mock.Mock(), mock.Mock(), mock.Mock())

        with self.assertRaises(NotImplementedError):
            setup_env_helper.build_config()

    def test__get_ports_gateway(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        setup_env_helper = SetupEnvHelper(vnfd_helper, mock.Mock(), mock.Mock())
        route = setup_env_helper._get_ports_gateway("xe0")
        self.assertEqual(route, "152.16.100.20")

    def test_setup_vnf_environment(self):
        setup_env_helper = SetupEnvHelper(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertIsNone(setup_env_helper.setup_vnf_environment())

    def test_tear_down(self):
        setup_env_helper = SetupEnvHelper(mock.Mock(), mock.Mock(), mock.Mock())

        with self.assertRaises(NotImplementedError):
            setup_env_helper.tear_down()


class TestDpdkVnfSetupEnvHelper(unittest.TestCase):

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

    def test__update_packet_type(self):
        ip_pipeline_cfg = 'pkt_type = ipv4'
        pkt_type = {'pkt_type': '1'}

        expected = "pkt_type = 1"
        result = DpdkVnfSetupEnvHelper._update_packet_type(ip_pipeline_cfg, pkt_type)
        self.assertEqual(result, expected)

    def test__update_packet_type_no_op(self):
        ip_pipeline_cfg = 'pkt_type = ipv6'
        pkt_type = {'pkt_type': '1'}

        expected = "pkt_type = ipv6"
        result = DpdkVnfSetupEnvHelper._update_packet_type(ip_pipeline_cfg, pkt_type)
        self.assertEqual(result, expected)

    def test__update_packet_type_multi_op(self):
        ip_pipeline_cfg = 'pkt_type = ipv4\npkt_type = 1\npkt_type = ipv4'
        pkt_type = {'pkt_type': '1'}

        expected = 'pkt_type = 1\npkt_type = 1\npkt_type = 1'
        result = DpdkVnfSetupEnvHelper._update_packet_type(ip_pipeline_cfg, pkt_type)
        self.assertEqual(result, expected)

    def test__update_traffic_type(self):
        ip_pipeline_cfg = 'pkt_type = ipv4'

        traffic_options = {"vnf_type": DpdkVnfSetupEnvHelper.APP_NAME, 'traffic_type': 4}
        expected = "pkt_type = ipv4"
        result = DpdkVnfSetupEnvHelper._update_traffic_type(ip_pipeline_cfg, traffic_options)
        self.assertEqual(result, expected)

    def test__update_traffic_type_ipv6(self):
        ip_pipeline_cfg = 'pkt_type = ipv4'

        traffic_options = {"vnf_type": DpdkVnfSetupEnvHelper.APP_NAME, 'traffic_type': 6}
        expected = "pkt_type = ipv6"
        result = DpdkVnfSetupEnvHelper._update_traffic_type(ip_pipeline_cfg, traffic_options)
        self.assertEqual(result, expected)

    def test__update_traffic_type_not_app_name(self):
        ip_pipeline_cfg = 'traffic_type = 4'

        vnf_type = ''.join(["Not", DpdkVnfSetupEnvHelper.APP_NAME])
        traffic_options = {"vnf_type": vnf_type, 'traffic_type': 8}
        expected = "traffic_type = 8"
        result = DpdkVnfSetupEnvHelper._update_traffic_type(ip_pipeline_cfg, traffic_options)
        self.assertEqual(result, expected)

    def test__setup_hugepages(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '', ''
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)

        result = dpdk_setup_helper._setup_hugepages()
        expect_start_list = ['awk', 'awk', 'echo']
        expect_in_list = ['meminfo', 'nr_hugepages', '16']
        call_args_iter = (args[0][0] for args in ssh_helper.execute.call_args_list)
        self.assertIsNone(result)
        self.assertEqual(ssh_helper.execute.call_count, 3)
        for expect_start, expect_in, arg0 in zip(expect_start_list, expect_in_list, call_args_iter):
            self.assertTrue(arg0.startswith(expect_start))
            self.assertIn(expect_in, arg0)

    def test__setup_hugepages_2_mb(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '2048kB  ', ''
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)

        result = dpdk_setup_helper._setup_hugepages()
        expect_start_list = ['awk', 'awk', 'echo']
        expect_in_list = ['meminfo', 'nr_hugepages', '16384']
        call_args_iter = (args[0][0] for args in ssh_helper.execute.call_args_list)
        self.assertIsNone(result)
        self.assertEqual(ssh_helper.execute.call_count, 3)
        for expect_start, expect_in, arg0 in zip(expect_start_list, expect_in_list, call_args_iter):
            self.assertTrue(arg0.startswith(expect_start))
            self.assertIn(expect_in, arg0)

    def test__get_dpdk_port_num(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        expected = '0'
        result = dpdk_setup_helper._get_dpdk_port_num('xe0')
        self.assertEqual(result, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.open')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.find_relative_file')
    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.MultiPortConfig')
    def test_build_config(self, mock_multi_port_config_class, mock_find, _):
        mock_multi_port_config = mock_multi_port_config_class()
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.vnf_cfg = {}
        scenario_helper.all_options = {}
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper.all_ports = []

        dpdk_setup_helper.PIPELINE_COMMAND = expected = 'pipeline command'
        result = dpdk_setup_helper.build_config()
        self.assertEqual(result, expected)
        self.assertGreaterEqual(ssh_helper.upload_config_file.call_count, 2)
        self.assertGreaterEqual(mock_find.call_count, 1)
        self.assertGreaterEqual(mock_multi_port_config.generate_config.call_count, 1)
        self.assertGreaterEqual(mock_multi_port_config.generate_script.call_count, 1)

    def test__build_pipeline_kwargs(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.provision_tool.return_value = 'tool_path'
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper.CFG_CONFIG = 'config'
        dpdk_setup_helper.CFG_SCRIPT = 'script'
        dpdk_setup_helper.all_ports = [3, 4, 5]
        dpdk_setup_helper.pipeline_kwargs = {}

        expected = {
            'cfg_file': 'config',
            'script': 'script',
            'ports_len_hex': '0xf',
            'tool_path': 'tool_path',
        }
        dpdk_setup_helper._build_pipeline_kwargs()
        self.assertDictEqual(dpdk_setup_helper.pipeline_kwargs, expected)

    def test__get_app_cpu(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.provision_tool.return_value = 'tool_path'
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)

        dpdk_setup_helper.CORES = expected = [5, 4, 3]
        result = dpdk_setup_helper._get_app_cpu()
        self.assertEqual(result, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.CpuSysCores')
    def test__get_app_cpu_no_cores_sw(self, mock_cpu_sys_cores_class):
        mock_cpu_sys_cores = mock_cpu_sys_cores_class()
        mock_cpu_sys_cores.get_core_socket.return_value = {
            'socket': [2, 4, 8, 10, 12],
        }
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.provision_tool.return_value = 'tool_path'
        scenario_helper = mock.Mock()
        scenario_helper.vnf_cfg = {
            'worker_threads': '2',
        }
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper.CORES = []
        dpdk_setup_helper.SW_DEFAULT_CORE = 1
        dpdk_setup_helper.HW_DEFAULT_CORE = 2
        dpdk_setup_helper.socket = 'socket'

        expected = [2, 4, 8]
        result = dpdk_setup_helper._get_app_cpu()
        self.assertEqual(result, expected)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.CpuSysCores')
    def test__get_app_cpu_no_cores_hw(self, mock_cpu_sys_cores_class):
        mock_cpu_sys_cores = mock_cpu_sys_cores_class()
        mock_cpu_sys_cores.get_core_socket.return_value = {
            'socket': [2, 4, 8, 10, 12],
        }
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.vnf_cfg = {
            'worker_threads': '2',
            'lb_config': 'HW',
        }
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper.CORES = []
        dpdk_setup_helper.SW_DEFAULT_CORE = 1
        dpdk_setup_helper.HW_DEFAULT_CORE = 2
        dpdk_setup_helper.socket = 'socket'

        expected = [2, 4, 8, 10]
        result = dpdk_setup_helper._get_app_cpu()
        self.assertEqual(result, expected)

    def test__get_cpu_sibling_list(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.side_effect = iter([(0, '5', ''), (0, '3,4', ''), (0, '10', '')])
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper._get_app_cpu = mock.Mock(return_value=[])

        expected = ['5', '3', '4', '10']
        result = dpdk_setup_helper._get_cpu_sibling_list([1, 3, 7])
        self.assertEqual(result, expected)

    def test__get_cpu_sibling_list_no_core_arg(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.side_effect = iter([(0, '5', ''), (0, '3,4', ''), (0, '10', '')])
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper._get_app_cpu = mock.Mock(return_value=[1, 7])

        expected = ['5', '3', '4']
        result = dpdk_setup_helper._get_cpu_sibling_list()
        self.assertEqual(result, expected)

    def test__get_cpu_sibling_list_ssh_failure(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.side_effect = iter([(0, '5', ''), SSHError, (0, '10', '')])
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper._get_app_cpu = mock.Mock(return_value=[])

        expected = []
        result = dpdk_setup_helper._get_cpu_sibling_list([1, 3, 7])
        self.assertEqual(result, expected)

    def test__validate_cpu_cfg(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.side_effect = iter([(0, '5', ''), (0, '3,4', ''), (0, '10', '')])
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper._get_app_cpu = mock.Mock(return_value=[1, 3, 7])

        expected = ['5', '3', '4', '10']
        result = dpdk_setup_helper._validate_cpu_cfg()
        self.assertEqual(result, expected)

    def test__find_used_drivers(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        stdout = '''
00:01.2 foo drv=name1
00:01.4 drv foo=name2
00:02.2 drv=name3
00:02.3 drv=name4
'''
        ssh_helper.execute.return_value = 0, stdout, ''
        scenario_helper = mock.Mock()
        dpdk_setup_helper = DpdkVnfSetupEnvHelper(vnfd_helper, ssh_helper, scenario_helper)
        dpdk_setup_helper.used_drivers = None
        dpdk_setup_helper._dpdk_nic_bind = ''
        dpdk_setup_helper.bound_pci = [
            'pci 00:01.2',
            'pci 00:02.3',
        ]

        expected = {
            '00:01.2': (0, 'name1'),
            '00:02.3': (2, 'name4'),
        }
        dpdk_setup_helper._find_used_drivers()
        self.assertEqual(dpdk_setup_helper.used_drivers, expected)


class TestSampleVnf(unittest.TestCase):

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

    def test_get_port0localip6(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0)
        expected = '0064:ff9b:0:0:0:0:9810:6414'
        result = sample_vnf._get_port0localip6()
        self.assertEqual(result, expected)

    def test_get_port1localip6(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0)
        expected = '0064:ff9b:0:0:0:0:9810:2814'
        result = sample_vnf._get_port1localip6()
        self.assertEqual(result, expected)

    def test_get_port0prefixip6(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0)
        expected = '112'
        result = sample_vnf._get_port0prefixlen6()
        self.assertEqual(result, expected)

    def test_get_port1prefixip6(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0)
        expected = '112'
        result = sample_vnf._get_port1prefixlen6()
        self.assertEqual(result, expected)

    def test_get_port0gateway6(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0)
        expected = '0064:ff9b:0:0:0:0:9810:6414'
        result = sample_vnf._get_port0gateway6()
        self.assertEqual(result, expected)

    def test_get_port1gateway6(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0)
        expected = '0064:ff9b:0:0:0:0:9810:2814'
        result = sample_vnf._get_port1gateway6()
        self.assertEqual(result, expected)
