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

from __future__ import absolute_import
import mock
import unittest

from tests.unit.test_case import STL_MOCKS
from tests.unit.benchmark.contexts.test_standalone import StandaloneContextTestCase
from yardstick import ssh

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.benchmark.contexts.standalone.ovsdpdk import OvsdpdkStandalone

DRIVER = "i40e"
VF_NIC = "i40evf"

PCI_LIST = [
    '0000:06:00.0',
    '0000:06:00.1',
]

VPORTS_MAC_LIST = [
    '00:00:00:71:7d:25',
    '00:00:00:71:7d:26',
]

NIC_INPUT = {
    'interface': {},
    'vports_mac': VPORTS_MAC_LIST,
    'pci': PCI_LIST,
    'phy_driver': 'i40e'}

NIC_DETAILS = {
    'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
    'vports_mac': VPORTS_MAC_LIST,
    'pci': PCI_LIST,
    'phy_driver': 'i40e'}

CORRECT_FILE_PATH = "/etc/yardstick/nodes/pod_ovs.yaml"
WRONG_FILE_PATH = "/etc/yardstick/wrong.yaml"

OVS_NODES_KEY_FILE = [
    {
        'name': 'ovs',
        'ssh_port': 22,
        'ip': '10.10.10.11',
        'key_filename': '/root/.ssh/id_rsa',
        'vports_mac': [
            '00:00:00:00:00:03',
            '00:00:00:00:00:04',
        ],
        'vpath': '/usr/local/',
        'role': 'Ovsdpdk',
        'user': 'root',
        'images': '/var/lib/libvirt/images/ubuntu1.img',
        'flow': [
            'ovs-ofctl add-flow br0 in_port=1,action=output:3',
            'ovs-ofctl add-flow br0 in_port=3,action=output:1',
            'ovs-ofctl add-flow br0 in_port=4,action=output:2',
            'ovs-ofctl add-flow br0 in_port=2,action=output:4',
        ],
        'phy_driver': 'i40e',
        'phy_ports': PCI_LIST,
    },
]

OVS_NODES_PASSWORD = [
    {
        'name': 'ovs',
        'vports_mac': [
            '00:00:00:00:00:03',
            '00:00:00:00:00:04',
        ],
        'ip': '10.10.10.11',
        'role': 'Ovsdpdk',
        'user': 'root',
        'vpath': '/usr/local/',
        'images': '/var/lib/libvirt/images/ubuntu1.img',
        'flow': [
            'ovs-ofctl add-flow br0 in_port=1,action=output:3',
            'ovs-ofctl add-flow br0 in_port=3,action=output:1',
            'ovs-ofctl add-flow br0 in_port=4,action=output:2',
            'ovs-ofctl add-flow br0 in_port=2,action=output:4',
        ],
        'phy_driver': 'i40e',
        'password': 'password',
        'phy_ports': PCI_LIST,
    },
]


@mock.patch('yardstick.benchmark.contexts.standalone.time')
@mock.patch('yardstick.benchmark.contexts.standalone.ovsdpdk.time')
class OvsdpdkTestCase(StandaloneContextTestCase):

    FILE_OBJ = __file__

    NODES_SAMPLE_SSH = "ovs_sample_ssh_key.yaml"
    NODES_SAMPLE_PASSWORD = "ovs_sample_password.yaml"

    def setUp(self):
        self.test_context = OvsdpdkStandalone()

    def test_construct(self, *_):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertFalse(self.test_context.vm_deploy)
        self.assertTrue(self.test_context.first_run)

    @mock.patch("yardstick.ssh.SSH")
    def test_init_with_ssh(self, mock_ssh, *_):
        attrs = self.make_attrs(filename=self.NODES_SAMPLE_SSH)

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        self.test_context._ssh_helper = ssh_mock

        self.test_context.init(attrs)

    @mock.patch("yardstick.ssh.SSH")
    def test_init_with_password(self, mock_ssh, *_):
        attrs = self.make_attrs(filename=self.NODES_SAMPLE_PASSWORD)

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        self.test_context._ssh_helper = ssh_mock

        self.test_context.init(attrs)

    def test_init_bad_name(self, *_):
        with self.assertRaises(KeyError):
            self.test_context.init({})

    def test_init_bad_file(self, *_):
        attrs = self.make_attrs(filename=WRONG_FILE_PATH)
        with self.assertRaises(IOError):
            self.test_context.init(attrs)

    @mock.patch("yardstick.ssh.SSH")
    def test__install_required_libraries(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        ovs_obj = OvsdpdkStandalone()
        ovs_obj.first_run = True
        ovs_obj._ssh_helper = ssh_mock

        self.assertIsNone(ovs_obj._install_required_libraries())

    @mock.patch("yardstick.ssh.SSH")
    def test__setup_context(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        node0_nic_details = {'phy_ports': {"eth0 eth1"}}, NIC_DETAILS

        ovs_obj = OvsdpdkStandalone()
        ovs_obj._ssh_helper = ssh_mock
        ovs_obj.nodes = OVS_NODES_KEY_FILE
        ovs_obj.get_nic_details = mock.Mock(return_value=node0_nic_details)

        self.assertIsNone(ovs_obj._setup_context())

    @mock.patch("yardstick.ssh.SSH")
    def test_start_ovs_serverswitch(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        ovs_obj = OvsdpdkStandalone()
        ovs_obj._ssh_helper = ssh_mock
        ovs_obj.nodes = OVS_NODES_KEY_FILE

        self.assertIsNone(ovs_obj._start_ovs_serverswitch())

    @mock.patch("yardstick.ssh.SSH")
    def test_setup_ovs_bridge(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        ovs_obj = OvsdpdkStandalone()
        ovs_obj._ssh_helper = ssh_mock
        ovs_obj.nodes = OVS_NODES_KEY_FILE

        self.assertIsNone(ovs_obj._setup_ovs_bridge())

    @mock.patch("yardstick.ssh.SSH")
    def test_add_oflows(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        ovs_obj = OvsdpdkStandalone()
        ovs_obj._ssh_helper = ssh_mock
        ovs_obj.nodes = OVS_NODES_KEY_FILE

        self.assertIsNone(ovs_obj._add_oflows())

    @mock.patch("yardstick.ssh.SSH")
    def test__setup_context_vm_already_present(self, mock_ssh, *_):
        node0_nic_details = {'phy_ports': {"eth0 eth1"}}, NIC_DETAILS

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "vm1", ""
        mock_ssh.return_value = ssh_mock

        self.test_context._ssh_helper = ssh_mock
        self.test_context.nodes = OVS_NODES_KEY_FILE
        self.test_context._ssh_helper = ssh_mock
        self.test_context.get_nic_details = mock.Mock(return_value=node0_nic_details)

        self.assertIsNone(self.test_context._setup_context())

    @mock.patch("yardstick.ssh.SSH")
    def test__setup_context_vm_created(self, mock_ssh, *_):
        node0_nic_details = {'phy_ports': {"eth0 eth1"}}, NIC_DETAILS

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        ssh_mock.put.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        self.test_context._ssh_helper = ssh_mock
        self.test_context.nodes = OVS_NODES_KEY_FILE
        self.test_context.get_nic_details = mock.Mock(return_value=node0_nic_details)

        self.assertIsNone(self.test_context._setup_context())

    @mock.patch("yardstick.ssh.SSH")
    def test_destroy_vm_successful(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        ovs_obj = OvsdpdkStandalone()
        ovs_obj._ssh_helper= ssh_mock
        ovs_obj.nodes = OVS_NODES_KEY_FILE

        ssh_mock.execute.return_value = 0, "0 i40e", ""
        self.assertIsNone(ovs_obj.destroy_vm())

    @mock.patch("yardstick.ssh.SSH")
    def test_destroy_vm_unsuccessful(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        ovs_obj = OvsdpdkStandalone()
        ovs_obj._ssh_helper = ssh_mock
        ovs_obj.nodes = OVS_NODES_KEY_FILE

        ssh_mock.execute.return_value = 1, "", ""
        self.assertIsNone(ovs_obj.destroy_vm())


if __name__ == '__main__':
    unittest.main()
