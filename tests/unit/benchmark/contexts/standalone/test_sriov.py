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

import os
import unittest

import mock

from yardstick.benchmark.contexts.standalone import sriov

NIC_INPUT = {
    'interface': {},
    'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
    'pci': ['0000:06:00.0', '0000:06:00.1'],
    'phy_driver': 'i40e'}
DRIVER = "i40e"
NIC_DETAILS = {
    'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
    'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
    'pci': ['0000:06:00.0', '0000:06:00.1'],
    'phy_driver': 'i40e'}

CORRECT_FILE_PATH = "/etc/yardstick/nodes/pod_sriov.yaml"
WRONG_FILE_PATH = "/etc/yardstick/wrong.yaml"
SAMPLE_FILE = "sriov_sample_write_to_file.txt"

SRIOV = [{
    'auth_type': 'ssh_key',
    'name': 'sriov',
    'ssh_port': 22,
    'ip': '10.10.10.11',
    'key_filename': '/root/.ssh/id_rsa',
    'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
    'role': 'Sriov',
    'user': 'root',
    'images': '/var/lib/libvirt/images/ubuntu1.img',
    'phy_driver': 'i40e',
    'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

SRIOV_PASSWORD = [{
    'auth_type': 'password',
    'name': 'sriov',
    'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
    'ip': '10.10.10.11',
    'role': 'Sriov',
    'user': 'root',
    'images': '/var/lib/libvirt/images/ubuntu1.img',
    'phy_driver': 'i40e',
    'password': 'password',
    'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

vfnic = "i40evf"
PCIS = ['0000:06:00.0', '0000:06:00.1']


class SriovTestCase(unittest.TestCase):

    NODES_SAMPLE_SSH = "sriov_sample_ssh_key.yaml"
    NODES_SAMPLE_PASSWORD = "sriov_sample_password.yaml"

    def setUp(self):
        self.test_context = sriov.Sriov()

    def test_construct(self):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.sriov, [])
        self.assertFalse(self.test_context.vm_deploy)
        self.assertTrue(self.test_context.first_run)
        self.assertEqual(self.test_context.user, "")
        self.assertEqual(self.test_context.ssh_ip, "")
        self.assertEqual(self.test_context.passwd, "")
        self.assertEqual(self.test_context.ssh_port, "")
        self.assertEqual(self.test_context.auth_type, "")

    def test_init(self):
        self.test_context.parse_pod_and_get_data = mock.Mock()
        self.test_context.file_path = CORRECT_FILE_PATH
        self.test_context.init()
        self.assertIsNone(self.test_context.init())

    def test_successful_init_with_ssh(self):
        CORRECT_FILE_PATH = self._get_file_abspath(self.NODES_SAMPLE_SSH)
        self.test_context.parse_pod_and_get_data(CORRECT_FILE_PATH)

    def test_successful_init_with_password(self):
        CORRECT_FILE_PATH = self._get_file_abspath(self.NODES_SAMPLE_PASSWORD)
        self.test_context.parse_pod_and_get_data(CORRECT_FILE_PATH)

    def test_unsuccessful_init(self):
        self.assertRaises(
            IOError,
            lambda: self.test_context.parse_pod_and_get_data(WRONG_FILE_PATH))

    @mock.patch('yardstick.network_services.utils.provision_tool', return_value="a")
    def test_ssh_connection(self, mock_prov):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "a", ""))
            ssh.return_value = ssh_mock
            mock_prov.provision_tool = mock.Mock()
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.sriov = SRIOV_PASSWORD
            self.assertIsNone(sriov_obj.ssh_remote_machine())

    @mock.patch('yardstick.network_services.utils.provision_tool', return_value="a")
    def test_ssh_connection_ssh_key(self, mock_prov):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "a", ""))
            ssh.return_value = ssh_mock
            mock_prov.provision_tool = mock.Mock()
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.sriov = SRIOV
            sriov_obj.key_filename = '/root/.ssh/id_rsa'
            self.assertIsNone(sriov_obj.ssh_remote_machine())

    def test_get_nic_details(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "eth0 eth1", ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.sriov = SRIOV
            sriov_obj.connection = ssh_mock
            self.assertIsNotNone(sriov_obj.get_nic_details())

    def test_install_req_libs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.first_run = True
            sriov_obj.connection = ssh_mock
            self.assertIsNone(sriov_obj.install_req_libs())

    def test_configure_nics_for_sriov(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            nic_details = {
                'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
                'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
                'pci': ['0000:06:00.0', '0000:06:00.1'],
                'phy_driver': 'i40e',
                'vf_pci': [{}, {}]}
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock((DRIVER), return_value=(0, "0 driver", ""))
            ssh.return_value = ssh_mock
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            for i in range(len(NIC_DETAILS['pci'])):
                ssh_mock.execute = \
                    mock.Mock(return_value=(0, {}, ""))
                ssh_mock.execute = \
                    mock.Mock(return_value=(0, {}, ""))
                sriov_obj = sriov.Sriov()
                sriov_obj.connection = ssh_mock
                ssh_mock.execute = \
                    mock.Mock(return_value=(
                        0,
                        "{'0':'06:02:00','1':'06:06:00'}",
                        ""))
                sriov_obj.get_vf_datas = mock.Mock(return_value={
                    '0000:06:00.0': '0000:06:02.0'})
                nic_details['vf_pci'][i] = sriov_obj.get_vf_datas.return_value
                vf_pci = [[], []]
                vf_pci[i] = sriov_obj.get_vf_datas.return_value
            with mock.patch("yardstick.benchmark.contexts.standalone.sriov.time"):
                self.assertIsNotNone(sriov_obj.configure_nics_for_sriov(DRIVER, NIC_DETAILS))

    def test_setup_sriov_context(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            nic_details = {
                'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
                'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
                'pci': ['0000:06:00.0', '0000:06:00.1'],
                'phy_driver': 'i40e',
                'vf_pci': [{'vf_pci': '06:02.00'}, {'vf_pci': '06:06.00'}]}
            vf = [{'vf_pci': '06:02.00'}, {'vf_pci': '06:06.00'}]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.sriov = SRIOV
            blacklist = "/etc/modprobe.d/blacklist.conf"
            self.assertEqual(vfnic, "i40evf")
            mock_sriov = mock.Mock()
            mock_sriov.sriov_obj.read_from_file(blacklist)
            sriov_obj.read_from_file = mock.Mock(
                return_value="some random text")
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            sriov_obj.configure_nics_for_sriov = mock.Mock(
                return_value=nic_details)
            nic_details = sriov_obj.configure_nics_for_sriov.return_value
            self.assertEqual(vf, nic_details['vf_pci'])
            vf = [
                {'vf_pci': '06:02.00', 'mac': '00:00:00:00:00:0a'},
                {'vf_pci': '06:06.00', 'mac': '00:00:00:00:00:0b'}]
            sriov_obj.add_sriov_interface = mock.Mock()
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.put = mock.Mock()
            sriov_obj.check_output = mock.Mock(return_value=(1, {}))
            with mock.patch("yardstick.benchmark.contexts.standalone.sriov.time"):
                self.assertIsNone(sriov_obj.setup_sriov_context(PCIS, nic_details, DRIVER))

    def test_setup_sriov_context_vm_already_present(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            nic_details = {
                'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
                'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
                'pci': ['0000:06:00.0', '0000:06:00.1'],
                'phy_driver': 'i40e',
                'vf_pci': [{'vf_pci': '06:02.00'}, {'vf_pci': '06:06.00'}]}
            vf = [{'vf_pci': '06:02.00'}, {'vf_pci': '06:06.00'}]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.sriov = SRIOV
            blacklist = "/etc/modprobe.d/blacklist.conf"
            self.assertEqual(vfnic, "i40evf")
            mock_sriov = mock.Mock()
            mock_sriov.sriov_obj.read_from_file(blacklist)
            sriov_obj.read_from_file = mock.Mock(
                return_value="some random text")
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            sriov_obj.configure_nics_for_sriov = mock.Mock(
                return_value=nic_details)
            nic_details = sriov_obj.configure_nics_for_sriov.return_value
            self.assertEqual(vf, nic_details['vf_pci'])
            vf = [
                {'vf_pci': '06:02.00', 'mac': '00:00:00:00:00:0a'},
                {'vf_pci': '06:06.00', 'mac': '00:00:00:00:00:0b'}]
            sriov_obj.add_sriov_interface = mock.Mock()
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.put = mock.Mock()
            sriov_obj.check_output = mock.Mock(return_value=(0, "vm1"))
            with mock.patch("yardstick.benchmark.contexts.standalone.sriov.time"):
                self.assertIsNone(sriov_obj.setup_sriov_context(PCIS, nic_details, DRIVER))

    @mock.patch(
        'yardstick.benchmark.contexts.standalone.sriov',
        return_value="Domain vm1 created from /tmp/vm_sriov.xml")
    def test_is_vm_created(self, NIC_INPUT):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            mock_sriov = mock.Mock()
            pcis = NIC_DETAILS['pci']
            driver = NIC_DETAILS['phy_driver']
            self.assertIsNotNone(
                mock_sriov.sriov_obj.setup_sriov_context(
                    pcis,
                    NIC_DETAILS,
                    driver))

    def test_add_sriov_interface(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            with mock.patch("xml.etree.ElementTree.parse") as parse:
                with mock.patch("re.search") as re:
                    with mock.patch("xml.etree.ElementTree.SubElement") \
                        as elem:
                            parse = mock.Mock(return_value="root")
                            re = mock.Mock()
                            elem = mock.Mock()
                            print("{0} {1} {2}".format(parse, re, elem))
                            self.assertIsNone(sriov_obj.add_sriov_interface(
                                0,
                                "0000:06:02.0",
                                "00:00:00:00:00:0a",
                                "/tmp/vm_sriov.xml"))

    def test_get_virtual_devices(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            pci_out = " \
            PCI_CLASS=20000 \
            PCI_ID=8086:154C \
            PCI_SUBSYS_ID=8086:0000 \
            PCI_SLOT_NAME=0000:06:02.0 \
            MODALIAS= \
            pci:v00008086d0000154Csv00008086sd00000000bc02sc00i00"
            pci = "0000:06:00.0"
            sriov_obj.check_output = mock.Mock(return_value=(0, pci_out))
            with mock.patch("re.search") as re:
                re = mock.Mock(return_value="a")
                print("{0}".format(re))
                self.assertIsNotNone(sriov_obj.get_virtual_devices(pci))

    def test_get_vf_datas(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.get_virtual_devices = mock.Mock(
                return_value={'0000:06:00.0': '0000:06:02.0'})
            with mock.patch("re.search") as re:
                re = mock.Mock()
                print("{0}".format(re))
                self.assertIsNotNone(sriov_obj.get_vf_datas(
                    'vf_pci',
                    {'0000:06:00.0': '0000:06:02.0'},
                    "00:00:00:00:00:0a"))

    def test_check_output(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            cmd = "command"
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            self.assertIsNotNone(sriov_obj.check_output(cmd, None))

    def test_split_cpu_list_available(self):
        with mock.patch("itertools.chain") as iter1:
            iter1 = mock.Mock()
            print("{0}".format(iter1))
            sriov_obj = sriov.Sriov()
            self.assertIsNotNone(sriov_obj.split_cpu_list('0,5'))

    def test_split_cpu_list_null(self):
        with mock.patch("itertools.chain") as iter1:
            iter1 = mock.Mock()
            print("{0}".format(iter1))
            sriov_obj = sriov.Sriov()
            self.assertEqual(sriov_obj.split_cpu_list([]), [])

    def test_destroy_vm_successful(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.sriov = SRIOV
            sriov_obj.check_output = mock.Mock(return_value=(0, "vm1"))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "0 i40e"))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "0 i40e"))
            self.assertIsNone(sriov_obj.destroy_vm())

    def test_destroy_vm_unsuccessful(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            sriov_obj.connection = ssh_mock
            sriov_obj.sriov = SRIOV
            sriov_obj.check_output = mock.Mock(return_value=(1, {}))
            self.assertIsNone(sriov_obj.destroy_vm())

    def test_read_from_file(self):
        CORRECT_FILE_PATH = self._get_file_abspath(self.NODES_SAMPLE_PASSWORD)
        sriov_obj = sriov.Sriov()
        self.assertIsNotNone(sriov_obj.read_from_file(CORRECT_FILE_PATH))

    def test_write_to_file(self):
        sriov_obj = sriov.Sriov()
        self.assertIsNone(sriov_obj.write_to_file(SAMPLE_FILE, "some content"))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

if __name__ == '__main__':
    unittest.main()
