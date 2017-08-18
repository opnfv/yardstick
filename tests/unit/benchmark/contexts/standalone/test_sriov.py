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

from tests.unit import STL_MOCKS
from tests.unit.benchmark.contexts.test_standalone import StandaloneContextTestCase
from yardstick import ssh

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.benchmark.contexts.standalone.sriov import SriovStandaloneContext

DRIVER = "i40e"
VF_NIC = "i40evf"

VF_MAC_LIST = [
    '00:00:00:71:7d:25',
    '00:00:00:71:7d:26',
]

PCI_LIST = [
    '0000:06:00.0',
    '0000:06:00.1',
]

NIC_INPUT = {
    'interface': {},
    'vf_macs': VF_MAC_LIST,
    'pci': PCI_LIST,
    'phy_driver': 'i40e',
}

NIC_DETAILS = {
    'interface': {
        0: 'enp6s0f0',
        1: 'enp6s0f1',
    },
    'vf_macs': VF_MAC_LIST,
    'pci': PCI_LIST,
    'phy_driver': 'i40e',
}

CORRECT_FILE_PATH = "/etc/yardstick/nodes/pod_sriov.yaml"
WRONG_FILE_PATH = "/etc/yardstick/wrong.yaml"
SAMPLE_FILE = "sriov_sample_write_to_file.txt"

SRIOV_NODES_KEY_FILE = [
    {
        'name': 'sriov',
        'ssh_port': 22,
        'ip': '10.10.10.11',
        'key_filename': '/root/.ssh/id_rsa',
        'vf_macs': VF_MAC_LIST,
        'role': 'Sriov',
        'user': 'root',
        'images': '/var/lib/libvirt/images/ubuntu1.img',
        'phy_driver': 'i40e',
        'phy_ports': PCI_LIST,
    },
]

SRIOV_NODES_PASSWORD = [
    {
        'name': 'sriov',
        'vf_macs': VF_MAC_LIST,
        'ip': '10.10.10.11',
        'role': 'Sriov',
        'user': 'root',
        'images': '/var/lib/libvirt/images/ubuntu1.img',
        'phy_driver': 'i40e',
        'password': 'password',
        'phy_ports': PCI_LIST,
    },
]


@mock.patch('yardstick.benchmark.contexts.standalone.time')
@mock.patch('yardstick.benchmark.contexts.standalone.sriov.time')
class SriovTestCase(StandaloneContextTestCase):

    FILE_OBJ = __file__

    NODES_SAMPLE_SSH = "sriov_sample_ssh_key.yaml"
    NODES_SAMPLE_PASSWORD = "sriov_sample_password.yaml"

    def setUp(self):
        self.test_context = SriovStandaloneContext()

    def test___init__(self, *_):
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
    def test_init_with_password(self, mock_ssh_type, *_):
        attrs = self.make_attrs(filename=self.NODES_SAMPLE_PASSWORD)

        ssh_mock_instance = self.mock_ssh(mock_ssh_type)
        self.test_context._ssh_helper = ssh_mock_instance

        self.test_context.init(attrs)

    def test_init_bad_name(self, *_):
        with self.assertRaises(KeyError):
            self.test_context.init({})

    def test_init_bad_file(self, *_):
        attrs = self.make_attrs(filename=WRONG_FILE_PATH)
        with self.assertRaises(IOError):
            self.test_context.init(attrs)

    @mock.patch("yardstick.ssh.SSH")
    def test__install_required_libraries(self, mock_ssh_type, *_):
        mock_ssh_instance = self.mock_ssh(mock_ssh_type)

        self.test_context.first_run = True
        self.test_context._ssh_helper = mock_ssh_instance
        self.assertIsNone(self.test_context._install_required_libraries())

    @mock.patch("yardstick.ssh.SSH")
    def test__configure_nics_for_sriov(self, mock_ssh_type, *_):
        match_vf_value = {'0000:06:00.0': '0000:06:02.0'}
        node0_nic_details = {'phy_driver': DRIVER}, NIC_DETAILS
        exec_result = 0, "{'0':'06:02:00','1':'06:06:00'}", ""

        mock_ssh_instance = self.mock_ssh(mock_ssh_type, exec_result=exec_result)

        self.test_context._ssh_helper = mock_ssh_instance
        self.test_context.match_vf_value = mock.Mock(return_value=match_vf_value)
        self.test_context.get_nic_details = mock.Mock(return_value=node0_nic_details)

        result = self.test_context._configure_nics_for_sriov()
        self.assertIsNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test__setup_context(self, mock_ssh, *_):
        nic_details = {
            'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'pci': ['0000:06:00.0', '0000:06:00.1'],
            'phy_driver': 'i40e',
            'vf_pci': [{'vf_pci': '06:02.00'}, {'vf_pci': '06:06.00'}],
        }

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        ssh_mock.put = mock.Mock()
        mock_ssh.return_value = ssh_mock

        node0_nic_details = {'phy_driver': DRIVER}, nic_details

        sriov_obj = SriovStandaloneContext()
        sriov_obj._ssh_helper = ssh_mock
        sriov_obj.nodes = SRIOV_NODES_KEY_FILE
        sriov_obj.read_from_file = mock.Mock(return_value="some random text")
        sriov_obj.configure_nics_for_sriov = mock.Mock(return_value=nic_details)
        sriov_obj.add_sriov_interface = mock.Mock()
        sriov_obj.get_nic_details = mock.Mock(return_value=node0_nic_details)

        result = sriov_obj._setup_context()
        self.assertIsNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test__setup_context_vm_already_present(self, mock_ssh, *_):
        nic_details = {
            'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
            'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
            'pci': ['0000:06:00.0', '0000:06:00.1'],
            'phy_driver': 'i40e',
            'vf_pci': [{'vf_pci': '06:02.00'}, {'vf_pci': '06:06.00'}],
        }

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        ssh_mock.put = mock.Mock()
        mock_ssh.return_value = ssh_mock

        node0_nic_details = {'phy_driver': DRIVER}, nic_details

        self.test_context._ssh_helper = ssh_mock
        self.test_context.nodes = SRIOV_NODES_KEY_FILE
        self.test_context.read_from_file = mock.Mock(return_value="some random text")
        self.test_context.configure_nics_for_sriov = mock.Mock(return_value=nic_details)
        self.test_context.add_sriov_interface = mock.Mock()
        self.test_context.get_nic_details = mock.Mock(return_value=node0_nic_details)

        result = self.test_context._setup_context()
        self.assertIsNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test_add_sriov_interface(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        sriov_obj = SriovStandaloneContext()
        sriov_obj._ssh_helper = ssh_mock

        parse_mocking = mock.patch("xml.etree.ElementTree.parse")
        re_mocking = mock.patch("re.search")
        xml_mocking = mock.patch("xml.etree.ElementTree.SubElement")

        with parse_mocking, re_mocking, xml_mocking:
            result = sriov_obj.add_sriov_interface(0, "0000:06:02.0",
                                                   "00:00:00:00:00:0a", "/tmp/vm_sriov.xml")

        self.assertIsNone(result)

    @mock.patch("re.search")
    @mock.patch("yardstick.ssh.SSH")
    def test_get_vf_datas(self, mock_ssh, *_):
        virt_devs = {'0000:06:00.0': '0000:06:02.0'}

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        ssh_mock.get_virtual_devices.return_value = virt_devs
        mock_ssh.return_value = ssh_mock

        sriov_obj = SriovStandaloneContext()
        sriov_obj._ssh_helper = ssh_mock

        result = sriov_obj.match_vf_value(str(virt_devs), "00:00:00:00:00:0a")
        self.assertIsNotNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test_destroy_vm_successful(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        sriov_obj = SriovStandaloneContext()
        sriov_obj._ssh_helper = ssh_mock
        sriov_obj.nodes = SRIOV_NODES_KEY_FILE

        ssh_mock.execute.return_value = 0, "0 i40e", ""
        self.assertIsNone(sriov_obj.destroy_vm())

    @mock.patch("yardstick.ssh.SSH")
    def test_destroy_vm_unsuccessful(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        mock_ssh.return_value = ssh_mock

        sriov_obj = SriovStandaloneContext()
        sriov_obj._ssh_helper = ssh_mock
        sriov_obj.nodes = SRIOV_NODES_KEY_FILE

        self.assertIsNone(sriov_obj.destroy_vm())

    def dup_test_read_from_file(self, *_):
        correct_file_path = self.get_file_abspath(self.NODES_SAMPLE_PASSWORD)
        self.assertIsNotNone(SriovStandaloneContext.read_from_file(correct_file_path))

    def dup_test_write_to_file(self):
        self.assertIsNone(SriovStandaloneContext.write_to_file(SAMPLE_FILE, "some content"))

    @mock.patch("yardstick.ssh.SSH")
    def test_deploy_sriov_first_time(self, mock_ssh, *_):
        attrs = self.make_attrs('foo', self.NODES_SAMPLE_PASSWORD)
        virt_devs = {'0000:06:00.0': '0000:06:02.0'}

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        ssh_mock.get_virtual_devices.return_value = virt_devs
        mock_ssh.return_value = ssh_mock

        node0_nic_details = {'phy_driver': DRIVER}, NIC_DETAILS

        self.test_context._ssh_helper = ssh_mock
        self.test_context.vm_deploy = True
        self.test_context.get_nic_details = mock.Mock(return_value=node0_nic_details)
        self.test_context.add_sriov_interface = mock.Mock()
        self.test_context.init(attrs)

        self.assertIsNone(self.test_context.deploy())

    @mock.patch("yardstick.ssh.SSH")
    def test_deploy_sriov_not_first_time(self, mock_ssh, *_):
        attrs = self.make_attrs('foo', self.NODES_SAMPLE_PASSWORD)
        virt_devs = {'0000:06:00.0': '0000:06:02.0'}

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "", ""
        ssh_mock.get_virtual_devices.return_value = virt_devs
        mock_ssh.return_value = ssh_mock

        node0_nic_details = {'phy_driver': DRIVER}, NIC_DETAILS

        self.test_context.vm_deploy = True
        self.test_context._ssh_helper = ssh_mock
        self.test_context.get_nic_details = mock.Mock(return_value=node0_nic_details)
        self.test_context.add_sriov_interface = mock.Mock()
        self.test_context.init(attrs)

        self.assertIsNone(self.test_context.deploy())


if __name__ == '__main__':
    unittest.main()
