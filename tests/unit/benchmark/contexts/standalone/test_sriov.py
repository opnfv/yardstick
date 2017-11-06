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

# Unittest for yardstick.benchmark.contexts.standalone.standalonesriov

from __future__ import absolute_import
from copy import deepcopy
import os
import unittest
import mock

from yardstick.common import utils
from yardstick.benchmark.contexts.standalone import sriov


class SriovContextTestCase(unittest.TestCase):

    NODES_SAMPLE = "nodes_sample.yaml"
    NODES_SRIOV_SAMPLE = "nodes_sriov_sample.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample.yaml"

    ATTRS = {
        'name': 'StandaloneSriov',
        'file': 'pod',
        'flavor': {},
        'servers': {},
        'networks': {},
    }

    NETWORKS = {
        'mgmt': {'cidr': '152.16.100.10/24'},
        'private_0': {
            'phy_port': '0000:05:00.0',
            'vpci': '0000:00:07.0',
            'cidr': '152.16.100.10/24',
            'interface': 'if0',
            'mac': '00:00:00:00:00:01',
            'vf_pci': {
                'vf_pci': 0,
            },
            'gateway_ip': '152.16.100.20',
        },
        'public_0': {
            'phy_port': '0000:05:00.1',
            'vpci': '0000:00:08.0',
            'cidr': '152.16.40.10/24',
            'interface': 'if0',
            'vf_pci': {
                'vf_pci': 0,
            },
            'mac': '00:00:00:00:00:01',
            'gateway_ip': '152.16.100.20',
        },
    }

    def setUp(self):
        utils.MethodCallsOrder.ENABLED = False
        self.sriov = sriov.SriovContext()

    def test___init__(self):
        self.assertIsNone(self.sriov.file_path)
        self.assertEqual(self.sriov.first_run, True)

    @mock.patch('yardstick.benchmark.contexts.standalone.base.model')
    def test_init(self, mock_model):
        mock_model.parse_pod_file.return_value = [{}, [{}], {}]
        self.assertIsNone(self.sriov.init(self.ATTRS))

    @mock.patch('yardstick.ssh.SSH')
    def Test_deploy(self, mock_ssh):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock

        self.sriov.vm_deploy = False
        self.assertIsNone(self.sriov.deploy())

        self.sriov.vm_deploy = True
        self.sriov.host_mgmt = {}
        self.sriov.install_req_libs = mock.Mock()
        self.sriov.get_nic_details = mock.Mock(return_value={})
        self.sriov.setup_context = mock.Mock(return_value={})
        self.sriov.wait_for_vnfs_to_start = mock.Mock(return_value={})
        self.assertIsNone(self.sriov.deploy())

    @mock.patch('yardstick.ssh.SSH')
    def test_undeploy(self, mock_ssh):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock

        self.sriov.vm_deploy = False
        self.assertIsNone(self.sriov.undeploy())

        self.sriov.vm_deploy = True
        self.sriov.connection = ssh_mock
        self.sriov.vm_names = ['vm_0', 'vm_1']
        self.sriov.drivers = ['vm_0', 'vm_1']
        self.sriov.networks = deepcopy(self.NETWORKS)
        self.assertIsNone(self.sriov.undeploy())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test__get_server_with_dic_attr_name(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SRIOV_SAMPLE)
        }

        self.sriov.init(attrs)

        attr_name = {'name': 'foo.bar'}
        result = self.sriov._get_server(attr_name)

        self.assertEqual(result, None)

    @mock.patch('yardstick.benchmark.contexts.standalone.model')
    def test__get_server_not_found(self, mock_model):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SRIOV_SAMPLE)
        }

        mock_model.parse_pod_file.return_value = [{}, {}, {}]
        self.sriov.init(attrs)

        attr_name = 'bar.foo'
        result = self.sriov._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_mismatch(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SRIOV_SAMPLE)
        }

        self.sriov.init(attrs)

        attr_name = 'bar.foo1'
        result = self.sriov._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_duplicate(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)
        }

        self.sriov.init(attrs)

        attr_name = 'node1.foo'
        with self.assertRaises(ValueError):
            self.sriov._get_server(attr_name)

    def test__get_server_found(self):
        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SRIOV_SAMPLE)
        }

        self.sriov.init(attrs)

        attr_name = 'node1.foo'
        result = self.sriov._get_server(attr_name)

        self.assertEqual(result['ip'], '10.229.47.137')
        self.assertEqual(result['name'], 'node1.foo')
        self.assertEqual(result['user'], 'root')
        self.assertEqual(result['key_filename'], '/root/.yardstick_key')

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
        self.sriov.networks = {
            'a': network1,
            'b': network2,
        }

        attr_name = {}
        self.assertIsNone(self.sriov._get_network(attr_name))

        attr_name = {'vld_id': 'vld777'}
        self.assertIsNone(self.sriov._get_network(attr_name))

        self.assertIsNone(self.sriov._get_network(None))

        attr_name = 'vld777'
        self.assertIsNone(self.sriov._get_network(attr_name))

        attr_name = {'vld_id': 'vld999'}
        expected = {
            "name": 'net_2',
            "vld_id": 'vld999',
            "segmentation_id": None,
            "network_type": None,
            "physical_network": None,
        }
        result = self.sriov._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = network1
        result = self.sriov._get_network(attr_name)
        self.assertDictEqual(result, expected)

    def test__configure_nics(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.sriov.vm_deploy = True
        self.sriov.connection = ssh_mock
        self.sriov.vm_names = ['vm_0', 'vm_1']
        self.sriov.drivers = []
        self.sriov.networks = deepcopy(self.NETWORKS)
        self.sriov._get_vf_data = mock.Mock(return_value="")
        self.assertIsNone(self.sriov._configure_nics())

    @mock.patch('yardstick.benchmark.contexts.standalone.sriov.model')
    def test__enable_interfaces(self, mock_libvirt):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.sriov.vm_deploy = True
        self.sriov.connection = ssh_mock
        self.sriov.vm_names = ['vm_0', 'vm_1']
        self.sriov.drivers = []
        self.sriov.networks = deepcopy(self.NETWORKS)
        self.sriov._get_vf_data = mock.Mock(return_value="")
        self.assertIsNone(self.sriov._enable_interfaces(0, 0, ["private_0"], 'test'))

    @mock.patch('yardstick.benchmark.contexts.standalone.base.model')
    def test_setup_context(self, mock_libvirt):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock

        self.sriov.vm_deploy = True
        self.sriov.connection = ssh_mock
        self.sriov.vm_names = ['vm_0', 'vm_1']
        self.sriov.drivers = []
        self.sriov.servers = {
            'vnf_0': {
                'network_ports': {
                    'mgmt': {'cidr': '152.16.100.10/24'},
                    'xe0': ['private_0'],
                    'xe1': ['public_0']
                }
            }
        }
        self.sriov.networks = deepcopy(self.NETWORKS)
        self.sriov.host_mgmt = {}
        self.sriov.flavor = {}
        self.sriov.configure_nics = mock.Mock(return_value="")
        mock_libvirt.build_vm_xml = mock.Mock(return_value=[6, "00:00:00:00:00:01"])
        self.sriov._enable_interfaces = mock.Mock(return_value="")
        self.sriov.cloud_init = mock.Mock()
        self.sriov.cloud_init.enabled.return_value = True
        self.assertIsNotNone(self.sriov.setup_context())

    def test__get_vf_data(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.sriov.vm_deploy = True
        self.sriov.connection = ssh_mock
        self.sriov.vm_names = ['vm_0', 'vm_1']
        self.sriov.drivers = []
        self.sriov.servers = {
            'vnf_0': {
                'network_ports': {
                    'mgmt': {'cidr': '152.16.100.10/24'},
                    'xe0': ['private_0'],
                    'xe1': ['public_0']
                }
            }
        }
        self.sriov.networks = deepcopy(self.NETWORKS)
        self.assertIsNotNone(self.sriov._get_vf_data("", "0000:00:01.0",
                                                     "00:00:00:00:00:01", "if0"))
