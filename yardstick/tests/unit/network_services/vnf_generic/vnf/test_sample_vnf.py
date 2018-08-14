# Copyright (c) 2017-2018 Intel Corporation
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

import unittest
import mock
import six
import time
import subprocess

import paramiko

from yardstick.common import exceptions as y_exceptions
from yardstick.common import utils
from yardstick.network_services.nfvi import resource
from yardstick.network_services.vnf_generic.vnf import base
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import vnf_ssh_helper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.tests.unit.network_services.vnf_generic.vnf import test_base
from yardstick.benchmark.contexts import base as ctx_base
from yardstick import ssh


class MockError(Exception):
    pass


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
                            'dpdk_port_num': 0,
                            'driver': 'i40e',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.20',
                            'local_mac': '00:00:00:00:00:01',
                            'vld_id': 'uplink_0',
                            'ifname': 'xe0',
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0'
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.1',
                            'dpdk_port_num': 1,
                            'driver': 'ixgbe',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_mac': '00:00:00:00:00:02',
                            'vld_id': 'downlink_0',
                            'ifname': 'xe1',
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

    def setUp(self):
        self.ssh_helper = vnf_ssh_helper.VnfSshHelper(
            self.VNFD_0['mgmt-interface'], 'my/bin/path')
        self.ssh_helper._run = mock.Mock()

    def assertAll(self, iterable, message=None):
        self.assertTrue(all(iterable), message)

    def test_get_class(self):
        self.assertIs(vnf_ssh_helper.VnfSshHelper.get_class(),
                      vnf_ssh_helper.VnfSshHelper)

    @mock.patch.object(ssh, 'paramiko')
    def test_copy(self, _):
        self.ssh_helper.execute('ls')
        self.assertTrue(self.ssh_helper.is_connected)
        result = self.ssh_helper.copy()
        self.assertIsInstance(result, vnf_ssh_helper.VnfSshHelper)
        self.assertFalse(result.is_connected)
        self.assertEqual(result.bin_path, self.ssh_helper.bin_path)
        self.assertEqual(result.host, self.ssh_helper.host)
        self.assertEqual(result.port, self.ssh_helper.port)
        self.assertEqual(result.user, self.ssh_helper.user)
        self.assertEqual(result.password, self.ssh_helper.password)
        self.assertEqual(result.key_filename, self.ssh_helper.key_filename)

    @mock.patch.object(paramiko, 'SSHClient')
    def test_upload_config_file(self, mock_paramiko):
        self.assertFalse(self.ssh_helper.is_connected)
        cfg_file = self.ssh_helper.upload_config_file('/my/prefix', 'my content')
        self.assertTrue(self.ssh_helper.is_connected)
        mock_paramiko.assert_called_once()
        self.assertEqual(cfg_file, '/my/prefix')

    @mock.patch.object(paramiko, 'SSHClient')
    def test_upload_config_file_path_does_not_exist(self, mock_paramiko):
        self.assertFalse(self.ssh_helper.is_connected)
        cfg_file = self.ssh_helper.upload_config_file('my/prefix', 'my content')
        self.assertTrue(self.ssh_helper.is_connected)
        mock_paramiko.assert_called_once()
        self.assertTrue(cfg_file.startswith('/tmp'))

    def test_join_bin_path(self):
        expected_start = 'my'
        expected_middle_list = ['bin']
        expected_end = 'path'
        result = self.ssh_helper.join_bin_path()
        self.assertTrue(result.startswith(expected_start))
        self.assertAll(middle in result for middle in expected_middle_list)
        self.assertTrue(result.endswith(expected_end))

        expected_middle_list.append(expected_end)
        expected_end = 'some_file.sh'
        result = self.ssh_helper.join_bin_path('some_file.sh')
        self.assertTrue(result.startswith(expected_start))
        self.assertAll(middle in result for middle in expected_middle_list)
        self.assertTrue(result.endswith(expected_end))

        expected_middle_list.append('some_dir')
        expected_end = 'some_file.sh'
        result = self.ssh_helper.join_bin_path('some_dir', 'some_file.sh')
        self.assertTrue(result.startswith(expected_start))
        self.assertAll(middle in result for middle in expected_middle_list)
        self.assertTrue(result.endswith(expected_end))

    @mock.patch.object(paramiko, 'SSHClient')
    @mock.patch.object(ssh, 'provision_tool')
    def test_provision_tool(self, mock_provision_tool, mock_paramiko):
        self.assertFalse(self.ssh_helper.is_connected)
        self.ssh_helper.provision_tool()
        self.assertTrue(self.ssh_helper.is_connected)
        mock_paramiko.assert_called_once()
        mock_provision_tool.assert_called_once()

        self.ssh_helper.provision_tool(tool_file='my_tool.sh')
        self.assertTrue(self.ssh_helper.is_connected)
        mock_paramiko.assert_called_once()
        self.assertEqual(mock_provision_tool.call_count, 2)

        self.ssh_helper.provision_tool('tool_path', 'my_tool.sh')
        self.assertTrue(self.ssh_helper.is_connected)
        mock_paramiko.assert_called_once()
        self.assertEqual(mock_provision_tool.call_count, 3)


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
                            'dpdk_port_num': 0,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.20',
                            'local_mac': '00:00:00:00:00:01',
                            'vld_id': 'uplink_0',
                            'ifname': 'xe0',
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
                            'local_mac': '00:00:00:00:00:02',
                            'vld_id': 'downlink_0',
                            'ifname': 'xe1',
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

    def test_setup_vnf_environment(self):
        setup_env_helper = SetupEnvHelper(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertIsNone(setup_env_helper.setup_vnf_environment())

    def test_tear_down(self):
        setup_env_helper = SetupEnvHelper(mock.Mock(), mock.Mock(), mock.Mock())

        with self.assertRaises(NotImplementedError):
            setup_env_helper.tear_down()


class TestDpdkVnfSetupEnvHelper(unittest.TestCase):

    VNFD_0 = TestVnfSshHelper.VNFD_0

    VNFD = TestVnfSshHelper.VNFD

    def setUp(self):
        self.vnfd_helper = base.VnfdHelper(deepcopy(self.VNFD_0))
        self.scenario_helper = mock.Mock()
        self.ssh_helper = mock.Mock()
        self.dpdk_setup_helper = sample_vnf.DpdkVnfSetupEnvHelper(
            self.vnfd_helper, self.ssh_helper, self.scenario_helper)

    def test__update_packet_type(self):
        ip_pipeline_cfg = 'pkt_type = ipv4'
        pkt_type = {'pkt_type': '1'}

        expected = "pkt_type = 1"
        result = self.dpdk_setup_helper._update_packet_type(
            ip_pipeline_cfg, pkt_type)
        self.assertEqual(result, expected)

    def test__update_packet_type_no_op(self):
        ip_pipeline_cfg = 'pkt_type = ipv6'
        pkt_type = {'pkt_type': '1'}

        expected = "pkt_type = ipv6"
        result = self.dpdk_setup_helper._update_packet_type(
            ip_pipeline_cfg, pkt_type)
        self.assertEqual(result, expected)

    def test__update_packet_type_multi_op(self):
        ip_pipeline_cfg = 'pkt_type = ipv4\npkt_type = 1\npkt_type = ipv4'
        pkt_type = {'pkt_type': '1'}
        expected = 'pkt_type = 1\npkt_type = 1\npkt_type = 1'

        result = self.dpdk_setup_helper._update_packet_type(
            ip_pipeline_cfg, pkt_type)
        self.assertEqual(result, expected)

    def test__update_traffic_type(self):
        ip_pipeline_cfg = 'pkt_type = ipv4'
        traffic_options = {
            "vnf_type": sample_vnf.DpdkVnfSetupEnvHelper.APP_NAME,
            "traffic_type": 4}
        expected = "pkt_type = ipv4"

        result = self.dpdk_setup_helper._update_traffic_type(
            ip_pipeline_cfg, traffic_options)
        self.assertEqual(result, expected)

    def test__update_traffic_type_ipv6(self):
        ip_pipeline_cfg = 'pkt_type = ipv4'
        traffic_options = {
            "vnf_type": sample_vnf.DpdkVnfSetupEnvHelper.APP_NAME,
            "traffic_type": 6}
        expected = "pkt_type = ipv6"

        result = self.dpdk_setup_helper._update_traffic_type(
            ip_pipeline_cfg, traffic_options)
        self.assertEqual(result, expected)

    def test__update_traffic_type_not_app_name(self):
        ip_pipeline_cfg = 'traffic_type = 4'
        vnf_type = ''.join(["Not", sample_vnf.DpdkVnfSetupEnvHelper.APP_NAME])
        traffic_options = {"vnf_type": vnf_type, 'traffic_type': 8}
        expected = "traffic_type = 8"

        result = self.dpdk_setup_helper._update_traffic_type(
            ip_pipeline_cfg, traffic_options)
        self.assertEqual(result, expected)

    @mock.patch.object(six, 'BytesIO', return_value=six.BytesIO(b'100\n'))
    @mock.patch.object(utils, 'read_meminfo',
                       return_value={'Hugepagesize': '2048'})
    def test__setup_hugepages_no_hugepages_defined(self, mock_meminfo, *args):
        self.scenario_helper.all_options = {}
        with mock.patch.object(sample_vnf.LOG, 'info') as mock_info:
            self.dpdk_setup_helper._setup_hugepages()
            mock_info.assert_called_once_with(
                'Hugepages size (kB): %s, number claimed: %s, number set: '
                '%s', 2048, 8192, 100)
        mock_meminfo.assert_called_once_with(self.ssh_helper)

    @mock.patch.object(six, 'BytesIO', return_value=six.BytesIO(b'100\n'))
    @mock.patch.object(utils, 'read_meminfo',
                       return_value={'Hugepagesize': '1048576'})
    def test__setup_hugepages_8gb_hugepages_defined(self, mock_meminfo, *args):
        self.scenario_helper.all_options = {'hugepages_gb': 8}
        with mock.patch.object(sample_vnf.LOG, 'info') as mock_info:
            self.dpdk_setup_helper._setup_hugepages()
            mock_info.assert_called_once_with(
                'Hugepages size (kB): %s, number claimed: %s, number set: '
                '%s', 1048576, 8, 100)
        mock_meminfo.assert_called_once_with(self.ssh_helper)

    @mock.patch.object(six.moves.builtins, 'open')
    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch.object(sample_vnf, 'MultiPortConfig')
    def test_build_config(self, mock_multi_port_config_class,
                          mock_find, *args):
        mock_multi_port_config = mock_multi_port_config_class()
        self.scenario_helper.vnf_cfg = {}
        self.scenario_helper.options = {}
        self.scenario_helper.all_options = {}

        self.dpdk_setup_helper.PIPELINE_COMMAND = expected = 'pipeline command'
        result = self.dpdk_setup_helper.build_config()
        self.assertEqual(result, expected)
        self.assertGreaterEqual(self.ssh_helper.upload_config_file.call_count, 2)
        mock_find.assert_called()
        mock_multi_port_config.generate_config.assert_called()
        mock_multi_port_config.generate_script.assert_called()

    @mock.patch.object(six.moves.builtins, 'open')
    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch.object(sample_vnf, 'MultiPortConfig')
    @mock.patch.object(utils, 'open_relative_file')
    def test_build_config2(self, mock_open_rf, mock_multi_port_config_class,
                          mock_find, *args):
        mock_multi_port_config = mock_multi_port_config_class()
        self.scenario_helper.options = {'rules': 'fake_file'}
        self.scenario_helper.vnf_cfg = {'file': 'fake_file'}
        self.scenario_helper.all_options = {}
        mock_open_rf.side_effect = mock.mock_open(read_data='fake_data')
        self.dpdk_setup_helper.PIPELINE_COMMAND = expected = 'pipeline command'

        result = self.dpdk_setup_helper.build_config()

        mock_open_rf.assert_called()
        self.assertEqual(result, expected)
        self.assertGreaterEqual(self.ssh_helper.upload_config_file.call_count, 2)
        mock_find.assert_called()
        mock_multi_port_config.generate_config.assert_called()
        mock_multi_port_config.generate_script.assert_called()

    def test__build_pipeline_kwargs(self):
        self.ssh_helper.provision_tool.return_value = 'tool_path'
        self.dpdk_setup_helper.CFG_CONFIG = 'config'
        self.dpdk_setup_helper.CFG_SCRIPT = 'script'
        self.dpdk_setup_helper.pipeline_kwargs = {}
        self.dpdk_setup_helper.all_ports = [0, 1, 2]
        self.dpdk_setup_helper.scenario_helper.vnf_cfg = {'lb_config': 'HW',
                                                          'worker_threads': 1}

        expected = {
            'cfg_file': 'config',
            'script': 'script',
            'port_mask_hex': '0x3',
            'tool_path': 'tool_path',
            'hwlb': ' --hwlb 1',
        }
        self.dpdk_setup_helper._build_pipeline_kwargs()
        self.assertDictEqual(self.dpdk_setup_helper.pipeline_kwargs, expected)

    @mock.patch.object(ssh, 'SSH')
    def test_setup_vnf_environment(self, *args):
        self.scenario_helper.nodes = [None, None]

        def execute(cmd):
            if cmd.startswith('which '):
                return exec_failure
            return exec_success

        exec_success = (0, 'good output', '')
        exec_failure = (1, 'bad output', 'error output')
        self.ssh_helper.execute = execute

        self.dpdk_setup_helper._validate_cpu_cfg = mock.Mock(return_value=[])

        with mock.patch.object(self.dpdk_setup_helper, '_setup_dpdk'):
            self.assertIsInstance(
                self.dpdk_setup_helper.setup_vnf_environment(),
                resource.ResourceProfile)

    def test__setup_dpdk(self):
        self.ssh_helper.execute = mock.Mock()
        self.ssh_helper.execute.return_value = (0, 0, 0)

        with mock.patch.object(self.dpdk_setup_helper, '_setup_hugepages') as \
                mock_setup_hp:
            self.dpdk_setup_helper._setup_dpdk()
        mock_setup_hp.assert_called_once()
        self.ssh_helper.execute.assert_has_calls([
            mock.call('sudo modprobe uio && sudo modprobe igb_uio'),
            mock.call('lsmod | grep -i igb_uio')
        ])

    @mock.patch.object(ssh, 'SSH')
    def test__setup_resources(self, _):
        self.dpdk_setup_helper._validate_cpu_cfg = mock.Mock()
        self.dpdk_setup_helper.bound_pci = [v['virtual-interface']["vpci"] for v in
                                            self.vnfd_helper.interfaces]
        result = self.dpdk_setup_helper._setup_resources()
        self.assertIsInstance(result, resource.ResourceProfile)
        self.assertEqual(self.dpdk_setup_helper.socket, 0)

    @mock.patch.object(ssh, 'SSH')
    def test__setup_resources_socket_1(self, _):
        self.vnfd_helper.interfaces[0]['virtual-interface']['vpci'] = \
            '0000:55:00.0'
        self.vnfd_helper.interfaces[1]['virtual-interface']['vpci'] = \
            '0000:35:00.0'

        self.dpdk_setup_helper._validate_cpu_cfg = mock.Mock()
        self.dpdk_setup_helper.bound_pci = [v['virtual-interface']["vpci"] for v in
                                            self.vnfd_helper.interfaces]
        result = self.dpdk_setup_helper._setup_resources()
        self.assertIsInstance(result, resource.ResourceProfile)
        self.assertEqual(self.dpdk_setup_helper.socket, 1)

    @mock.patch.object(time, 'sleep')
    def test__detect_and_bind_drivers(self, *args):
        self.scenario_helper.nodes = [None, None]
        rv = ['0000:05:00.1', '0000:05:00.0']

        self.dpdk_setup_helper.dpdk_bind_helper._get_bound_pci_addresses = \
            mock.Mock(return_value=rv)
        self.dpdk_setup_helper.dpdk_bind_helper.bind = mock.Mock()
        self.dpdk_setup_helper.dpdk_bind_helper.read_status = mock.Mock()

        self.assertIsNone(self.dpdk_setup_helper._detect_and_bind_drivers())

        intf_0 = self.vnfd_helper.vdu[0]['external-interface'][0]['virtual-interface']
        intf_1 = self.vnfd_helper.vdu[0]['external-interface'][1]['virtual-interface']
        self.assertEqual(0, intf_0['dpdk_port_num'])
        self.assertEqual(1, intf_1['dpdk_port_num'])

    def test_tear_down(self):
        self.scenario_helper.nodes = [None, None]

        self.dpdk_setup_helper.dpdk_bind_helper.bind = mock.Mock()
        self.dpdk_setup_helper.dpdk_bind_helper.used_drivers = {
            'd1': ['0000:05:00.0'],
            'd3': ['0000:05:01.0'],
        }

        self.assertIsNone(self.dpdk_setup_helper.tear_down())
        self.dpdk_setup_helper.dpdk_bind_helper.bind.assert_any_call(
            ['0000:05:00.0'], 'd1', True)
        self.dpdk_setup_helper.dpdk_bind_helper.bind.assert_any_call(
            ['0000:05:01.0'], 'd3', True)


class TestResourceHelper(unittest.TestCase):

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
                            'driver': 'i40e',
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
                            'driver': 'ixgbe',
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

    def setUp(self):
        self.vnfd_helper = base.VnfdHelper(self.VNFD_0)
        self.dpdk_setup_helper = sample_vnf.DpdkVnfSetupEnvHelper(
            self.vnfd_helper, mock.Mock(), mock.Mock())
        self.resource_helper = sample_vnf.ResourceHelper(self.dpdk_setup_helper)

    def test_setup(self):
        resource = object()
        self.dpdk_setup_helper.setup_vnf_environment = (
            mock.Mock(return_value=resource))
        resource_helper = sample_vnf.ResourceHelper(self.dpdk_setup_helper)

        self.assertIsNone(resource_helper.setup())
        self.assertIs(resource_helper.resource, resource)

    def test_generate_cfg(self):
        self.assertIsNone(self.resource_helper.generate_cfg())

    def test_stop_collect(self):
        self.resource_helper.resource = mock.Mock()

        self.assertIsNone(self.resource_helper.stop_collect())

    def test_stop_collect_none(self):
        self.resource_helper.resource = None

        self.assertIsNone(self.resource_helper.stop_collect())


class TestClientResourceHelper(unittest.TestCase):

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
                            'driver': 'i40e',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 0,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.100.20',
                            'local_mac': '00:00:00:00:00:01',
                            'vld_id': 'uplink_0',
                            'ifname': 'xe0',
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0'
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.1',
                            'driver': 'ixgbe',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 1,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_mac': '00:00:00:00:00:02',
                            'vld_id': 'downlink_0',
                            'ifname': 'xe1',
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1'
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:13',
                            'vpci': '0000:05:00.2',
                            'driver': 'ixgbe',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': 2,
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.30',
                            'local_mac': '00:00:00:00:00:11'
                        },
                        'vnfd-connection-point-ref': 'xe2',
                        'name': 'xe2'
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
            ],
        },
    }

    def setUp(self):
        vnfd_helper = base.VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        dpdk_setup_helper = sample_vnf.DpdkVnfSetupEnvHelper(
            vnfd_helper, ssh_helper, scenario_helper)
        self.client_resource_helper = (
            sample_vnf.ClientResourceHelper(dpdk_setup_helper))

    @mock.patch.object(sample_vnf, 'LOG')
    @mock.patch.object(sample_vnf, 'STLError', new_callable=lambda: MockError)
    def test_get_stats_not_connected(self, mock_stl_error, *args):
        self.client_resource_helper.client = mock.Mock()
        self.client_resource_helper.client.get_stats.side_effect = \
            mock_stl_error

        self.assertEqual(self.client_resource_helper.get_stats(), {})
        self.client_resource_helper.client.get_stats.assert_called_once()

    def test_clear_stats(self):
        self.client_resource_helper.client = mock.Mock()

        self.assertIsNone(self.client_resource_helper.clear_stats())
        self.assertEqual(
            self.client_resource_helper.client.clear_stats.call_count, 1)

    def test_clear_stats_of_ports(self):
        self.client_resource_helper.client = mock.Mock()

        self.assertIsNone(self.client_resource_helper.clear_stats([3, 4]))
        self.client_resource_helper.client.clear_stats.assert_called_once()

    def test_start(self):
        self.client_resource_helper.client = mock.Mock()

        self.assertIsNone(self.client_resource_helper.start())
        self.client_resource_helper.client.start.assert_called_once()

    def test_start_ports(self):
        self.client_resource_helper.client = mock.Mock()

        self.assertIsNone(self.client_resource_helper.start([3, 4]))
        self.client_resource_helper.client.start.assert_called_once()

    def test_collect_kpi_with_queue(self):
        self.client_resource_helper._result = {
            'existing': 43,
            'replaceable': 12}
        self.client_resource_helper._queue = mock.Mock()
        self.client_resource_helper._queue.empty.return_value = False
        self.client_resource_helper._queue.get.return_value = {
            'incoming': 34,
            'replaceable': 99}

        expected = {
            'existing': 43,
            'incoming': 34,
            'replaceable': 99,
        }
        result = self.client_resource_helper.collect_kpi()
        self.assertEqual(result, expected)

    @mock.patch.object(time, 'sleep')
    @mock.patch.object(sample_vnf, 'STLError')
    def test__connect_with_failures(self, mock_stl_error, *args):
        client = mock.MagicMock()
        client.connect.side_effect = mock_stl_error(msg='msg')

        self.assertIs(self.client_resource_helper._connect(client), client)

    @mock.patch.object(sample_vnf.ClientResourceHelper, '_build_ports')
    @mock.patch.object(sample_vnf.ClientResourceHelper, '_run_traffic_once',
                       return_value=(True, mock.ANY))
    def test_run_traffic(self, mock_run_traffic_once, mock_build_ports):
        client_resource_helper = sample_vnf.ClientResourceHelper(mock.Mock())
        client = mock.Mock()
        traffic_profile = mock.Mock()
        mq_producer = mock.Mock()
        with mock.patch.object(client_resource_helper, '_connect') \
                as mock_connect, \
                mock.patch.object(client_resource_helper, '_terminated') \
                as mock_terminated:
            mock_connect.return_value = client
            type(mock_terminated).value = mock.PropertyMock(
                side_effect=[0, 1, 1, lambda x: x])
            client_resource_helper.run_traffic(traffic_profile, mq_producer)

        mock_build_ports.assert_called_once()
        traffic_profile.register_generator.assert_called_once()
        mq_producer.tg_method_started.assert_called_once()
        mq_producer.tg_method_finished.assert_called_once()
        mq_producer.tg_method_iteration.assert_called_once_with(1)
        mock_run_traffic_once.assert_called_once_with(traffic_profile)

    @mock.patch.object(sample_vnf.ClientResourceHelper, '_build_ports')
    @mock.patch.object(sample_vnf.ClientResourceHelper, '_run_traffic_once',
                       side_effect=Exception)
    def test_run_traffic_exception(self, mock_run_traffic_once,
                                   mock_build_ports):
        client_resource_helper = sample_vnf.ClientResourceHelper(mock.Mock())
        client = mock.Mock()
        traffic_profile = mock.Mock()
        mq_producer = mock.Mock()
        with mock.patch.object(client_resource_helper, '_connect') \
                as mock_connect, \
                mock.patch.object(client_resource_helper, '_terminated') \
                as mock_terminated:
            mock_connect.return_value = client
            type(mock_terminated).value = mock.PropertyMock(return_value=0)
            mq_producer.reset_mock()
            # NOTE(ralonsoh): "trex_stl_exceptions.STLError" is mocked
            with self.assertRaises(Exception):
                client_resource_helper.run_traffic(traffic_profile,
                                                   mq_producer)

        mock_build_ports.assert_called_once()
        traffic_profile.register_generator.assert_called_once()
        mock_run_traffic_once.assert_called_once_with(traffic_profile)
        mq_producer.tg_method_started.assert_called_once()
        mq_producer.tg_method_finished.assert_not_called()
        mq_producer.tg_method_iteration.assert_not_called()


class TestRfc2544ResourceHelper(unittest.TestCase):

    RFC2544_CFG_1 = {
        'latency': True,
        'correlated_traffic': True,
        'allowed_drop_rate': '0.1 - 0.15',
    }

    RFC2544_CFG_2 = {
        'allowed_drop_rate': '  0.25    -   0.05  ',
    }

    RFC2544_CFG_3 = {
        'allowed_drop_rate': '0.2',
    }

    RFC2544_CFG_4 = {
        'latency': True,
    }

    SCENARIO_CFG_1 = {
        'options': {
            'rfc2544': RFC2544_CFG_1,
        }
    }

    SCENARIO_CFG_2 = {
        'options': {
            'rfc2544': RFC2544_CFG_2,
        }
    }

    SCENARIO_CFG_3 = {
        'options': {
            'rfc2544': RFC2544_CFG_3,
        }
    }

    SCENARIO_CFG_4 = {
        'options': {
            'rfc2544': RFC2544_CFG_4,
        }
    }

    def setUp(self):
        self.scenario_helper = sample_vnf.ScenarioHelper('name1')
        self.rfc2544_resource_helper = \
            sample_vnf.Rfc2544ResourceHelper(self.scenario_helper)

    def test_property_rfc2544(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_1

        self.assertIsNone(self.rfc2544_resource_helper._rfc2544)
        self.assertEqual(self.rfc2544_resource_helper.rfc2544,
                         self.RFC2544_CFG_1)
        self.assertEqual(self.rfc2544_resource_helper._rfc2544,
                         self.RFC2544_CFG_1)
        # ensure that resource_helper caches
        self.scenario_helper.scenario_cfg = {}
        self.assertEqual(self.rfc2544_resource_helper.rfc2544,
                         self.RFC2544_CFG_1)

    def test_property_tolerance_high(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_1

        self.assertIsNone(self.rfc2544_resource_helper._tolerance_high)
        self.assertEqual(self.rfc2544_resource_helper.tolerance_high, 0.15)
        self.assertEqual(self.rfc2544_resource_helper._tolerance_high, 0.15)
        # ensure that resource_helper caches
        self.scenario_helper.scenario_cfg = {}
        self.assertEqual(self.rfc2544_resource_helper.tolerance_high, 0.15)

    def test_property_tolerance_low(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_1

        self.assertIsNone(self.rfc2544_resource_helper._tolerance_low)
        self.assertEqual(self.rfc2544_resource_helper.tolerance_low, 0.1)
        self.assertEqual(self.rfc2544_resource_helper._tolerance_low, 0.1)
        # ensure that resource_helper caches
        self.scenario_helper.scenario_cfg = {}
        self.assertEqual(self.rfc2544_resource_helper.tolerance_low, 0.1)

    def test_property_tolerance_high_range_swap(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_2

        self.assertEqual(self.rfc2544_resource_helper.tolerance_high, 0.25)

    def test_property_tolerance_low_range_swap(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_2

        self.assertEqual(self.rfc2544_resource_helper.tolerance_low, 0.05)

    def test_property_tolerance_high_not_range(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_3

        self.assertEqual(self.rfc2544_resource_helper.tolerance_high, 0.2)

    def test_property_tolerance_low_not_range(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_3

        self.assertEqual(self.rfc2544_resource_helper.tolerance_low, 0.2)

    def test_property_tolerance_high_default(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_4

        self.assertEqual(self.rfc2544_resource_helper.tolerance_high, 0.0001)

    def test_property_tolerance_low_default(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_4

        self.assertEqual(self.rfc2544_resource_helper.tolerance_low, 0.0001)

    def test_property_latency(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_1

        self.assertIsNone(self.rfc2544_resource_helper._latency)
        self.assertTrue(self.rfc2544_resource_helper.latency)
        self.assertTrue(self.rfc2544_resource_helper._latency)
        # ensure that resource_helper caches
        self.scenario_helper.scenario_cfg = {}
        self.assertTrue(self.rfc2544_resource_helper.latency)

    def test_property_latency_default(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_2

        self.assertFalse(self.rfc2544_resource_helper.latency)

    def test_property_correlated_traffic(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_1

        self.assertIsNone(self.rfc2544_resource_helper._correlated_traffic)
        self.assertTrue(self.rfc2544_resource_helper.correlated_traffic)
        self.assertTrue(self.rfc2544_resource_helper._correlated_traffic)
        # ensure that resource_helper caches
        self.scenario_helper.scenario_cfg = {}
        self.assertTrue(self.rfc2544_resource_helper.correlated_traffic)

    def test_property_correlated_traffic_default(self):
        self.scenario_helper.scenario_cfg = self.SCENARIO_CFG_2

        self.assertFalse(self.rfc2544_resource_helper.correlated_traffic)


class TestSampleVNFDeployHelper(unittest.TestCase):

    def setUp(self):
        self._mock_time_sleep = mock.patch.object(time, 'sleep')
        self.mock_time_sleep = self._mock_time_sleep.start()
        self._mock_check_output = mock.patch.object(subprocess, 'check_output')
        self.mock_check_output = self._mock_check_output.start()
        self.addCleanup(self._stop_mocks)

        self.ssh_helper = mock.Mock()
        self.sample_vnf_deploy_helper = sample_vnf.SampleVNFDeployHelper(
            mock.Mock(), self.ssh_helper)
        self.ssh_helper.join_bin_path.return_value = 'joined_path'
        self.ssh_helper.put.return_value = None

    def _stop_mocks(self):
        self._mock_time_sleep.stop()
        self._mock_check_output.stop()

    def test_deploy_vnfs_disabled(self):
        self.ssh_helper.execute.return_value = 1, 'bad output', 'error output'

        self.sample_vnf_deploy_helper.deploy_vnfs('name1')
        self.sample_vnf_deploy_helper.DISABLE_DEPLOY = True
        self.assertEqual(self.ssh_helper.execute.call_count, 5)
        self.ssh_helper.put.assert_called_once()

    def test_deploy_vnfs(self):
        self.ssh_helper.execute.return_value = 1, 'bad output', 'error output'
        self.sample_vnf_deploy_helper.DISABLE_DEPLOY = False

        self.sample_vnf_deploy_helper.deploy_vnfs('name1')
        self.assertEqual(self.ssh_helper.execute.call_count, 5)
        self.ssh_helper.put.assert_called_once()

    def test_deploy_vnfs_early_success(self):
        self.ssh_helper.execute.return_value = 0, 'output', ''
        self.sample_vnf_deploy_helper.DISABLE_DEPLOY = False

        self.sample_vnf_deploy_helper.deploy_vnfs('name1')
        self.ssh_helper.execute.assert_called_once()
        self.ssh_helper.put.assert_not_called()


class TestScenarioHelper(unittest.TestCase):

    def test_property_task_path(self):
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'task_path': 'my_path',
        }

        self.assertEqual(scenario_helper.task_path, 'my_path')

    def test_property_nodes(self):
        nodes = ['node1', 'node2']
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'nodes': nodes,
        }

        self.assertEqual(scenario_helper.nodes, nodes)

    def test_property_all_options(self):
        data = {
            'name1': {
                'key3': 'value3',
            },
            'name2': {}
        }
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'options': data,
        }

        self.assertDictEqual(scenario_helper.all_options, data)

    def test_property_options(self):
        data = {
            'key1': 'value1',
            'key2': 'value2',
        }
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'options': {
                'name1': data,
            },
        }

        self.assertDictEqual(scenario_helper.options, data)

    def test_property_vnf_cfg(self):
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'options': {
                'name1': {
                    'vnf_config': 'my_config',
                },
            },
        }

        self.assertEqual(scenario_helper.vnf_cfg, 'my_config')

    def test_property_vnf_cfg_default(self):
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'options': {
                'name1': {},
            },
        }

        self.assertDictEqual(scenario_helper.vnf_cfg, ScenarioHelper.DEFAULT_VNF_CFG)

    def test_property_topology(self):
        scenario_helper = ScenarioHelper('name1')
        scenario_helper.scenario_cfg = {
            'topology': 'my_topology',
        }

        self.assertEqual(scenario_helper.topology, 'my_topology')


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

    def test___init__(self):
        sample_vnf = SampleVNF('vnf1', self.VNFD_0, 'task_id')

        self.assertEqual(sample_vnf.name, 'vnf1')
        self.assertDictEqual(sample_vnf.vnfd_helper, self.VNFD_0)

        # test the default setup helper is SetupEnvHelper, not subclass
        self.assertEqual(type(sample_vnf.setup_helper), SetupEnvHelper)

        # test the default resource helper is ResourceHelper, not subclass
        self.assertEqual(type(sample_vnf.resource_helper), ResourceHelper)

    def test___init___alt_types(self):
        class MySetupEnvHelper(SetupEnvHelper):
            pass

        class MyResourceHelper(ResourceHelper):
            pass

        sample_vnf = SampleVNF('vnf1', self.VNFD_0, 'task_id',
                               MySetupEnvHelper, MyResourceHelper)

        self.assertEqual(sample_vnf.name, 'vnf1')
        self.assertDictEqual(sample_vnf.vnfd_helper, self.VNFD_0)

        # test the default setup helper is MySetupEnvHelper, not subclass
        self.assertEqual(type(sample_vnf.setup_helper), MySetupEnvHelper)

        # test the default resource helper is MyResourceHelper, not subclass
        self.assertEqual(type(sample_vnf.resource_helper), MyResourceHelper)

    @mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.Process')
    def test__start_vnf(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf._run = mock.Mock()

        self.assertIsNone(sample_vnf.queue_wrapper)
        self.assertIsNone(sample_vnf._vnf_process)
        self.assertIsNone(sample_vnf._start_vnf())
        self.assertIsNotNone(sample_vnf.queue_wrapper)
        self.assertIsNotNone(sample_vnf._vnf_process)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server', return_value='fake_context')
    @mock.patch("yardstick.ssh.SSH")
    def test_instantiate(self, ssh, *args):
        test_base.mock_ssh(ssh)
        nodes = {
            'vnf1': 'name1',
            'vnf2': 'name2',
        }

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.scenario_helper.scenario_cfg = {
            'nodes': {sample_vnf.name: 'mock'}
        }
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf._start_server = mock.Mock(return_value=0)
        sample_vnf._vnf_process = mock.MagicMock()
        sample_vnf._vnf_process._is_alive.return_value = 1
        sample_vnf.ssh_helper = mock.MagicMock()
        sample_vnf.deploy_helper = mock.MagicMock()
        sample_vnf.resource_helper.ssh_helper = mock.MagicMock()
        scenario_cfg = {
            'nodes': nodes,
        }

        self.assertIsNone(sample_vnf.instantiate(scenario_cfg, {}))

    def test__update_collectd_options(self):
        scenario_cfg = {'options':
                            {'collectd':
                                 {'interval': 3,
                                  'plugins':
                                      {'plugin3': {'param': 3}}},
                             'vnf__0':
                                 {'collectd':
                                      {'interval': 2,
                                       'plugins':
                                           {'plugin3': {'param': 2},
                                            'plugin2': {'param': 2}}}}}}
        context_cfg = {'nodes':
                           {'vnf__0':
                                {'collectd':
                                     {'interval': 1,
                                      'plugins':
                                          {'plugin3': {'param': 1},
                                           'plugin2': {'param': 1},
                                           'plugin1': {'param': 1}}}}}}
        expected = {'interval': 1,
                    'plugins':
                        {'plugin3': {'param': 1},
                         'plugin2': {'param': 1},
                         'plugin1': {'param': 1}}}

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf__0', vnfd, 'task_id')
        sample_vnf._update_collectd_options(scenario_cfg, context_cfg)
        self.assertEqual(sample_vnf.setup_helper.collectd_options, expected)

    def test__update_options(self):
        options1 = {'interval': 1,
                    'param1': 'value1',
                    'plugins':
                        {'plugin3': {'param': 3},
                         'plugin2': {'param': 1},
                         'plugin1': {'param': 1}}}
        options2 = {'interval': 2,
                    'param2': 'value2',
                    'plugins':
                        {'plugin4': {'param': 4},
                         'plugin2': {'param': 2},
                         'plugin1': {'param': 2}}}
        expected = {'interval': 1,
                    'param1': 'value1',
                    'param2': 'value2',
                    'plugins':
                        {'plugin4': {'param': 4},
                         'plugin3': {'param': 3},
                         'plugin2': {'param': 1},
                         'plugin1': {'param': 1}}}

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf._update_options(options2, options1)
        self.assertEqual(options2, expected)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch("yardstick.ssh.SSH")
    def test_wait_for_instantiate_empty_queue(self, ssh, *args):
        test_base.mock_ssh(ssh, exec_result=(1, "", ""))

        queue_size_list = [
            0,
            1,
            0,
            1,
        ]

        queue_get_list = [
            'some output',
            'pipeline> ',
        ]

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf.WAIT_TIME_FOR_SCRIPT = 0
        sample_vnf._start_server = mock.Mock(return_value=0)
        sample_vnf._vnf_process = mock.MagicMock()
        sample_vnf._vnf_process.exitcode = 0
        sample_vnf._vnf_process._is_alive.return_value = 1
        sample_vnf.queue_wrapper = mock.Mock()
        sample_vnf.q_out = mock.Mock()
        sample_vnf.q_out.qsize.side_effect = iter(queue_size_list)
        sample_vnf.q_out.get.side_effect = iter(queue_get_list)
        sample_vnf.ssh_helper = mock.MagicMock()
        sample_vnf.resource_helper.ssh_helper = mock.MagicMock()
        sample_vnf.resource_helper.start_collect = mock.MagicMock()

        self.assertEqual(sample_vnf.wait_for_instantiate(), 0)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_vnf_execute_with_queue_data(self, *args):
        queue_size_list = [
            1,
            1,
            0,
        ]

        queue_get_list = [
            'hello ',
            'world'
        ]

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf.q_out = mock.Mock()
        sample_vnf.q_out.qsize.side_effect = iter(queue_size_list)
        sample_vnf.q_out.get.side_effect = iter(queue_get_list)

        self.assertEqual(sample_vnf.vnf_execute('my command'), 'hello world')

    def test_terminate_without_vnf_process(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf.vnf_execute = mock.Mock()
        sample_vnf.ssh_helper = mock.Mock()
        sample_vnf._tear_down = mock.Mock()
        sample_vnf.resource_helper = mock.Mock()

        self.assertIsNone(sample_vnf.terminate())

    def test_get_stats(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf.APP_WORD = 'sample1'
        sample_vnf.vnf_execute = mock.Mock(return_value='the stats')

        self.assertEqual(sample_vnf.get_stats(), 'the stats')

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    def test_collect_kpi(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.scenario_helper.scenario_cfg = {
            'nodes': {sample_vnf.name: "mock"}
        }
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf.COLLECT_KPI = r'\s(\d+)\D*(\d+)\D*(\d+)'
        sample_vnf.COLLECT_MAP = {
            'k1': 3,
            'k2': 1,
            'k3': 2,
        }
        sample_vnf.get_stats = mock.Mock(return_value='index0: 34 -- 91, 27')
        sample_vnf.resource_helper = mock.Mock()
        sample_vnf.resource_helper.collect_kpi.return_value = {}

        expected = {
            'k1': 27,
            'k2': 34,
            'k3': 91,
            'collect_stats': {},
            'physical_node': 'mock_node'
        }
        result = sample_vnf.collect_kpi()
        self.assertDictEqual(result, expected)

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server', return_value='mock_node')
    def test_collect_kpi_default(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.scenario_helper.scenario_cfg = {
            'nodes': {sample_vnf.name: "mock"}
        }
        sample_vnf.APP_NAME = 'sample1'
        sample_vnf.COLLECT_KPI = r'\s(\d+)\D*(\d+)\D*(\d+)'
        sample_vnf.get_stats = mock.Mock(return_value='')

        expected = {
            'physical_node': 'mock_node',
            'packets_in': 0,
            'packets_fwd': 0,
            'packets_dropped': 0,
        }
        result = sample_vnf.collect_kpi()
        self.assertDictEqual(result, expected)

    def test_scale(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        self.assertRaises(y_exceptions.FunctionNotImplemented,
                          sample_vnf.scale)

    def test__run(self):
        test_cmd = 'test cmd'
        run_kwargs = {'arg1': 'val1', 'arg2': 'val2'}
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        sample_vnf = SampleVNF('vnf1', vnfd, 'task_id')
        sample_vnf.ssh_helper = mock.Mock()
        sample_vnf.setup_helper = mock.Mock()
        with mock.patch.object(sample_vnf, '_build_config',
                               return_value=test_cmd), \
                mock.patch.object(sample_vnf, '_build_run_kwargs'):
            sample_vnf.run_kwargs = run_kwargs
            sample_vnf._run()
        sample_vnf.ssh_helper.drop_connection.assert_called_once()
        sample_vnf.ssh_helper.run.assert_called_once_with(test_cmd,
                                                          **run_kwargs)
        sample_vnf.setup_helper.kill_vnf.assert_called_once()


class TestSampleVNFTrafficGen(unittest.TestCase):

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
                            'driver': 'i40e',
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
                            'driver': 'ixgbe',
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
            ],
        },
    }

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

    def test__check_status(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')

        with self.assertRaises(NotImplementedError):
            sample_vnf_tg._check_status()

    def test_listen_traffic(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')

        sample_vnf_tg.listen_traffic(mock.Mock())

    def test_verify_traffic(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')

        sample_vnf_tg.verify_traffic(mock.Mock())

    def test_terminate(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')
        sample_vnf_tg._traffic_process = mock.Mock()
        sample_vnf_tg._tg_process = mock.Mock()

        sample_vnf_tg.terminate()

    def test__wait_for_process(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')
        with mock.patch.object(sample_vnf_tg, '_check_status',
                               return_value=0) as mock_status, \
                mock.patch.object(sample_vnf_tg, '_tg_process') as mock_proc:
            mock_proc.is_alive.return_value = True
            mock_proc.exitcode = 234
            self.assertEqual(sample_vnf_tg._wait_for_process(), 234)
            mock_proc.is_alive.assert_called_once()
            mock_status.assert_called_once()

    def test__wait_for_process_not_alive(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')
        with mock.patch.object(sample_vnf_tg, '_tg_process') as mock_proc:
            mock_proc.is_alive.return_value = False
            self.assertRaises(RuntimeError, sample_vnf_tg._wait_for_process)
            mock_proc.is_alive.assert_called_once()

    def test__wait_for_process_delayed(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')
        with mock.patch.object(sample_vnf_tg, '_check_status',
                               side_effect=[1, 0]) as mock_status, \
                mock.patch.object(sample_vnf_tg,
                                  '_tg_process') as mock_proc:
            mock_proc.is_alive.return_value = True
            mock_proc.exitcode = 234
            self.assertEqual(sample_vnf_tg._wait_for_process(), 234)
            mock_proc.is_alive.assert_has_calls([mock.call(), mock.call()])
            mock_status.assert_has_calls([mock.call(), mock.call()])

    def test_scale(self):
        sample_vnf_tg = SampleVNFTrafficGen('tg1', self.VNFD_0, 'task_id')
        self.assertRaises(y_exceptions.FunctionNotImplemented,
                          sample_vnf_tg.scale)
