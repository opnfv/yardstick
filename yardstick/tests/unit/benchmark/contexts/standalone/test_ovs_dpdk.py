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

import io
import os

import mock
import six
import unittest

from yardstick.benchmark.contexts.standalone import model
from yardstick.benchmark.contexts.standalone import ovs_dpdk
from yardstick.common import exceptions
from yardstick.network_services import utils


class OvsDpdkContextTestCase(unittest.TestCase):

    NODES_SAMPLE = "nodes_sample.yaml"
    NODES_ovs_dpdk_SAMPLE = "nodes_ovs_dpdk_sample.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample.yaml"

    NETWORKS = {
        'mgmt': {'cidr': '152.16.100.10/24'},
        'private_0': {
            'phy_port': "0000:05:00.0",
            'vpci': "0000:00:07.0",
            'cidr': '152.16.100.10/24',
            'interface': 'if0',
            'mac': "00:00:00:00:00:01",
            'vf_pci': {'vf_pci': 0},
            'gateway_ip': '152.16.100.20'},
        'public_0': {
            'phy_port': "0000:05:00.1",
            'vpci': "0000:00:08.0",
            'cidr': '152.16.40.10/24',
            'interface': 'if0',
            'vf_pci': {'vf_pci': 0},
            'mac': "00:00:00:00:00:01",
            'gateway_ip': '152.16.100.20'},
    }

    def setUp(self):
        self.attrs = {
            'name': 'foo',
            'task_id': '1234567890',
            'file': self._get_file_abspath(self.NODES_ovs_dpdk_SAMPLE)
        }
        self.ovs_dpdk = ovs_dpdk.OvsDpdkContext()
        self.addCleanup(self._remove_contexts)

    def _remove_contexts(self):
        if self.ovs_dpdk in self.ovs_dpdk.list:
            self.ovs_dpdk._delete_context()

    @mock.patch('yardstick.benchmark.contexts.standalone.model.Server')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.StandaloneContextHelper')
    def test___init__(self, mock_helper, mock_server):
        self.ovs_dpdk.helper = mock_helper
        self.ovs_dpdk.vnf_node = mock_server
        self.assertIsNone(self.ovs_dpdk.file_path)
        self.assertTrue(self.ovs_dpdk.first_run)

    def test_init(self):
        ATTRS = {
            'name': 'StandaloneOvsDpdk',
            'task_id': '1234567890',
            'file': 'pod',
            'flavor': {},
            'servers': {},
            'networks': {},
        }

        self.ovs_dpdk.helper.parse_pod_file = mock.Mock(
            return_value=[{}, {}, {}])
        self.assertIsNone(self.ovs_dpdk.init(ATTRS))

    def test_setup_ovs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {}
            self.assertIsNone(self.ovs_dpdk.setup_ovs())

    def test_start_ovs_serverswitch(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {}
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.assertIsNone(self.ovs_dpdk.start_ovs_serverswitch())

    def test_setup_ovs_bridge_add_flows(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
            self.ovs_dpdk.connection = ssh_mock
            self.ovs_dpdk.networks = self.NETWORKS
            self.ovs_dpdk.ovs_properties = {
                'version': {'ovs': '2.7.0'}
            }
            self.ovs_dpdk.wait_for_vswitchd = 0
            self.assertIsNone(self.ovs_dpdk.setup_ovs_bridge_add_flows())

    @mock.patch("yardstick.ssh.SSH")
    def test_cleanup_ovs_dpdk_env(self, mock_ssh):
       mock_ssh.execute.return_value = 0, "a", ""
       self.ovs_dpdk.connection = mock_ssh
       self.ovs_dpdk.networks = self.NETWORKS
       self.ovs_dpdk.ovs_properties = {
           'version': {'ovs': '2.7.0'}
       }
       self.ovs_dpdk.wait_for_vswitchd = 0
       self.assertIsNone(self.ovs_dpdk.cleanup_ovs_dpdk_env())

    @mock.patch.object(ovs_dpdk.OvsDpdkContext, '_check_hugepages')
    @mock.patch.object(utils, 'get_nsb_option')
    @mock.patch.object(model.OvsDeploy, 'ovs_deploy')
    def test_check_ovs_dpdk_env(self, mock_ovs_deploy, mock_get_nsb_option,
                                mock_check_hugepages):
        self.ovs_dpdk.connection = mock.Mock()
        self.ovs_dpdk.connection.execute = mock.Mock(
            return_value=(1, 0, 0))
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.ovs_properties = {
            'version': {'ovs': '2.7.0', 'dpdk': '16.11.1'}
        }
        self.ovs_dpdk.wait_for_vswitchd = 0
        self.ovs_dpdk.cleanup_ovs_dpdk_env = mock.Mock()
        mock_get_nsb_option.return_value = 'fake_path'

        self.ovs_dpdk.check_ovs_dpdk_env()
        mock_ovs_deploy.assert_called_once()
        mock_check_hugepages.assert_called_once()
        mock_get_nsb_option.assert_called_once_with('bin_path')

    @mock.patch.object(ovs_dpdk.OvsDpdkContext, '_check_hugepages')
    def test_check_ovs_dpdk_env_wrong_version(self, mock_check_hugepages):
        self.ovs_dpdk.connection = mock.Mock()
        self.ovs_dpdk.connection.execute = mock.Mock(
            return_value=(1, 0, 0))
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.ovs_properties = {
            'version': {'ovs': '0.0.1', 'dpdk': '9.8.7'}
        }
        self.ovs_dpdk.wait_for_vswitchd = 0
        self.ovs_dpdk.cleanup_ovs_dpdk_env = mock.Mock()

        with self.assertRaises(exceptions.OVSUnsupportedVersion):
            self.ovs_dpdk.check_ovs_dpdk_env()
        mock_check_hugepages.assert_called_once()

    @mock.patch('yardstick.ssh.SSH')
    def test_deploy(self, *args):
        self.ovs_dpdk.vm_deploy = False
        self.assertIsNone(self.ovs_dpdk.deploy())

        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.host_mgmt = {}
        self.ovs_dpdk.install_req_libs = mock.Mock()
        self.ovs_dpdk.helper.get_nic_details = mock.Mock(return_value={})
        self.ovs_dpdk.check_ovs_dpdk_env = mock.Mock(return_value={})
        self.ovs_dpdk.setup_ovs = mock.Mock(return_value={})
        self.ovs_dpdk.start_ovs_serverswitch = mock.Mock(return_value={})
        self.ovs_dpdk.setup_ovs_bridge_add_flows = mock.Mock(return_value={})
        self.ovs_dpdk.setup_ovs_dpdk_context = mock.Mock(return_value={})
        self.ovs_dpdk.wait_for_vnfs_to_start = mock.Mock(return_value={})
        # TODO(elfoley): This test should check states/sideeffects instead of
        # output.
        self.assertIsNone(self.ovs_dpdk.deploy())

    @mock.patch.object(model.Libvirt, 'check_if_vm_exists_and_delete')
    def test_undeploy(self, mock_libvirt):
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = mock.Mock()
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = ['vm_0', 'vm_1']
        self.ovs_dpdk.cleanup_ovs_dpdk_env = mock.Mock()
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.undeploy()
        mock_libvirt.assert_has_calls([
            mock.call(self.ovs_dpdk.vm_names[0], self.ovs_dpdk.connection),
            mock.call(self.ovs_dpdk.vm_names[1], self.ovs_dpdk.connection)
        ])

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test__get_server_with_dic_attr_name(self):

        self.ovs_dpdk.init(self.attrs)

        attr_name = {'name': 'foo.bar'}
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_not_found(self):

        self.ovs_dpdk.helper.parse_pod_file = mock.Mock(
            return_value=[{}, {}, {}])
        self.ovs_dpdk.init(self.attrs)

        attr_name = 'bar.foo'
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_mismatch(self):

        self.ovs_dpdk.init(self.attrs)

        attr_name = 'bar.foo1'
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_duplicate(self):

        self.attrs['file'] = self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)

        self.ovs_dpdk.init(self.attrs)

        attr_name = 'node1.foo-12345678'
        with self.assertRaises(ValueError):
            self.ovs_dpdk._get_server(attr_name)

    def test__get_server_found(self):

        self.ovs_dpdk.init(self.attrs)

        attr_name = 'node1.foo-12345678'
        result = self.ovs_dpdk._get_server(attr_name)

        self.assertEqual(result['ip'], '10.229.47.137')
        self.assertEqual(result['name'], 'node1.foo-12345678')
        self.assertEqual(result['user'], 'root')
        self.assertEqual(result['key_filename'], '/root/.yardstick_key')

    # TODO(elfoley): Split this test for networks that exist and networks that
    #                don't
    def test__get_network(self):
        network1 = {
            'name': 'net_1',
            'vld_id': 'vld111',
            'segmentation_id': 'seg54',
            'network_type': 'type_a',
            'physical_network': 'phys',
        }
        network2 = {
            'name': 'net_2',
            'vld_id': 'vld999',
        }
        self.ovs_dpdk.networks = {
            'a': network1,
            'b': network2,
        }

        # Tests for networks that do not exist
        attr_name = {}
        self.assertIsNone(self.ovs_dpdk._get_network(attr_name))

        attr_name = {'vld_id': 'vld777'}
        self.assertIsNone(self.ovs_dpdk._get_network(attr_name))

        self.assertIsNone(self.ovs_dpdk._get_network(None))

        # TODO(elfoley): Split this test
        attr_name = 'vld777'
        self.assertIsNone(self.ovs_dpdk._get_network(attr_name))

        # Tests for networks that exist
        attr_name = {'vld_id': 'vld999'}
        expected = {
            "name": 'net_2',
            "vld_id": 'vld999',
            "segmentation_id": None,
            "network_type": None,
            "physical_network": None,
        }
        result = self.ovs_dpdk._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = network1
        result = self.ovs_dpdk._get_network(attr_name)
        self.assertDictEqual(result, expected)

    def test_configure_nics_for_ovs_dpdk(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = ssh_mock
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = []
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.helper.get_mac_address = mock.Mock(return_value="")
        self.ovs_dpdk.get_vf_datas = mock.Mock(return_value="")
        self.assertIsNone(self.ovs_dpdk.configure_nics_for_ovs_dpdk())

    @mock.patch.object(model.Libvirt, 'add_ovs_interface')
    def test__enable_interfaces(self, mock_add_ovs_interface):
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = mock.Mock()
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = []
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.ovs_properties = {'vpath': 'fake_path'}
        self.ovs_dpdk.get_vf_datas = mock.Mock(return_value="")
        self.ovs_dpdk._enable_interfaces(0, ["private_0"], 'test')
        mock_add_ovs_interface.assert_called_once_with(
            'fake_path', 0, self.NETWORKS['private_0']['vpci'],
            self.NETWORKS['private_0']['mac'], 'test')

    @mock.patch.object(model.Libvirt, 'build_vm_xml')
    @mock.patch.object(model.Libvirt, 'check_if_vm_exists_and_delete')
    @mock.patch.object(model.Libvirt, 'virsh_create_vm')
    def test_setup_ovs_dpdk_context(self, mock_create_vm, mock_check_if_exists,
                                    mock_build_xml):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.ovs_dpdk.vm_deploy = True
        self.ovs_dpdk.connection = ssh_mock
        self.ovs_dpdk.vm_names = ['vm_0', 'vm_1']
        self.ovs_dpdk.drivers = []
        self.ovs_dpdk.servers = {
            'vnf_0': {
                'network_ports': {
                    'mgmt': {'cidr': '152.16.100.10/24'},
                    'xe0': ['private_0'],
                    'xe1': ['public_0']
                }
            }
        }
        self.ovs_dpdk.networks = self.NETWORKS
        self.ovs_dpdk.host_mgmt = {}
        self.ovs_dpdk.flavor = {}
        self.ovs_dpdk.configure_nics_for_ovs_dpdk = mock.Mock(return_value="")
        mock_build_xml.return_value = [6, "00:00:00:00:00:01"]
        self.ovs_dpdk._enable_interfaces = mock.Mock(return_value="")
        vnf_instance = mock.Mock()
        self.ovs_dpdk.vnf_node.generate_vnf_instance = mock.Mock(
            return_value=vnf_instance)

        self.assertEqual([vnf_instance],
                         self.ovs_dpdk.setup_ovs_dpdk_context())
        mock_create_vm.assert_called_once_with(
            self.ovs_dpdk.connection, '/tmp/vm_ovs_0.xml')
        mock_check_if_exists.assert_called_once_with(
            'vm_0', self.ovs_dpdk.connection)
        mock_build_xml.assert_called_once_with(
            self.ovs_dpdk.connection, self.ovs_dpdk.vm_flavor,
            '/tmp/vm_ovs_0.xml', 'vm_0', 0)

    @mock.patch.object(io, 'BytesIO')
    def test__check_hugepages(self, mock_bytesio):
        data = six.BytesIO('HugePages_Total:      20\n'
                           'HugePages_Free:       20\n'
                           'HugePages_Rsvd:        0\n'
                           'HugePages_Surp:        0\n'
                           'Hugepagesize:    1048576 kB'.encode())
        mock_bytesio.return_value = data
        self.ovs_dpdk.connection = mock.Mock()
        self.ovs_dpdk._check_hugepages()

    @mock.patch.object(io, 'BytesIO')
    def test__check_hugepages_no_info(self, mock_bytesio):
        data = six.BytesIO(''.encode())
        mock_bytesio.return_value = data
        self.ovs_dpdk.connection = mock.Mock()
        with self.assertRaises(exceptions.OVSHugepagesInfoError):
            self.ovs_dpdk._check_hugepages()

    @mock.patch.object(io, 'BytesIO')
    def test__check_hugepages_no_total_hp(self, mock_bytesio):
        data = six.BytesIO('HugePages_Total:       0\n'
                           'HugePages_Free:        0\n'
                           'HugePages_Rsvd:        0\n'
                           'HugePages_Surp:        0\n'
                           'Hugepagesize:    1048576 kB'.encode())
        mock_bytesio.return_value = data
        self.ovs_dpdk.connection = mock.Mock()
        with self.assertRaises(exceptions.OVSHugepagesNotConfigured):
            self.ovs_dpdk._check_hugepages()

    @mock.patch.object(io, 'BytesIO')
    def test__check_hugepages_no_free_hp(self, mock_bytesio):
        data = six.BytesIO('HugePages_Total:      20\n'
                           'HugePages_Free:        0\n'
                           'HugePages_Rsvd:        0\n'
                           'HugePages_Surp:        0\n'
                           'Hugepagesize:    1048576 kB'.encode())
        mock_bytesio.return_value = data
        self.ovs_dpdk.connection = mock.Mock()
        with self.assertRaises(exceptions.OVSHugepagesZeroFree) as exc:
            self.ovs_dpdk._check_hugepages()
        self.assertEqual('There are no HugePages free in this system. Total '
                         'HugePages configured: 20', exc.exception.msg)
