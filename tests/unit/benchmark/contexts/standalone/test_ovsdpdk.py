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

from yardstick.benchmark.contexts.standalone import ovsdpdk

NIC_INPUT = {
    'interface': {},
    'vports_mac': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
    'pci': ['0000:06:00.0', '0000:06:00.1'],
    'phy_driver': 'i40e'}
DRIVER = "i40e"
NIC_DETAILS = {
    'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
    'vports_mac': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
    'pci': ['0000:06:00.0', '0000:06:00.1'],
    'phy_driver': 'i40e'}

CORRECT_FILE_PATH = "/etc/yardstick/nodes/pod_ovs.yaml"
WRONG_FILE_PATH = "/etc/yardstick/wrong.yaml"
SAMPLE_FILE = "ovs_sample_write_to_file.txt"

OVS = [{
    'auth_type': 'ssh_key',
    'name': 'ovs',
    'ssh_port': 22,
    'ip': '10.10.10.11',
    'key_filename': '/root/.ssh/id_rsa',
    'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
    'vpath': '/usr/local/',
    'role': 'Ovsdpdk',
    'user': 'root',
    'images': '/var/lib/libvirt/images/ubuntu1.img',
    'flow': ['ovs-ofctl add-flow br0 in_port=1,action=output:3',
             'ovs-ofctl add-flow br0 in_port=3,action=output:1',
             'ovs-ofctl add-flow br0 in_port=4,action=output:2',
             'ovs-ofctl add-flow br0 in_port=2,action=output:4'],
    'phy_driver': 'i40e',
    'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

OVS_PASSWORD = [{
    'auth_type': 'password',
    'name': 'ovs',
    'vports_mac': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
    'ip': '10.10.10.11',
    'role': 'Ovsdpdk',
    'user': 'root',
    'vpath': '/usr/local/',
    'images': '/var/lib/libvirt/images/ubuntu1.img',
    'flow': ['ovs-ofctl add-flow br0 in_port=1,action=output:3',
             'ovs-ofctl add-flow br0 in_port=3,action=output:1',
             'ovs-ofctl add-flow br0 in_port=4,action=output:2',
             'ovs-ofctl add-flow br0 in_port=2,action=output:4'],
    'phy_driver': 'i40e',
    'password': 'password',
    'phy_ports': ['0000:06:00.0', '0000:06:00.1']}]

#vfnic = "i40evf"
PCIS = ['0000:06:00.0', '0000:06:00.1']


class OvsdpdkTestCase(unittest.TestCase):

    NODES_SAMPLE_SSH = "ovs_sample_ssh_key.yaml"
    NODES_SAMPLE_PASSWORD = "ovs_sample_password.yaml"

    def setUp(self):
        self.test_context = ovsdpdk.Ovsdpdk()

    def test_construct(self):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.ovs, [])
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

    def test_ssh_connection(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock

    @mock.patch('yardstick.network_services.utils.provision_tool', return_value="b")
    def test_ssh_connection(self, mock_prov):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "b", ""))
            ssh.return_value = ssh_mock
            mock_prov.provision_tool = mock.Mock()
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.connection = ssh_mock
            ovs_obj.ovs = OVS_PASSWORD
            self.assertIsNone(ovs_obj.ssh_remote_machine())

    @mock.patch('yardstick.network_services.utils.provision_tool', return_value="b")
    def test_ssh_connection_ssh_key(self, mock_prov):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "b", ""))
            ssh.return_value = ssh_mock
            mock_prov.provision_tool = mock.Mock()
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.connection = ssh_mock
            ovs_obj.ovs = OVS
            ovs_obj.key_filename = '/root/.ssh/id_rsa'
            self.assertIsNone(ovs_obj.ssh_remote_machine())

    def test_get_nic_details(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "eth0 eth1", ""))
            ssh.return_value = ssh_mock
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.ovs = OVS
            ovs_obj.connection = ssh_mock
            self.assertIsNotNone(ovs_obj.get_nic_details())

    def test_install_req_libs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.first_run = True
            ovs_obj.connection = ssh_mock
            self.assertIsNone(ovs_obj.install_req_libs())

    def test_setup_ovs(self):
            with mock.patch("yardstick.ssh.SSH") as ssh:
                ssh_mock = mock.Mock(autospec=ssh.SSH)
                ssh_mock.execute = \
                    mock.Mock(return_value=(0, {}, ""))
                ssh.return_value = ssh_mock
                ovs_obj = ovsdpdk.Ovsdpdk()
                ovs_obj.connection = ssh_mock
                ovs_obj.ovs = OVS
                self.assertIsNone(ovs_obj.setup_ovs({"eth0 eth1"}))

    def test_start_ovs_serverswitch(self):
         with mock.patch("yardstick.ssh.SSH") as ssh:
             ssh_mock = mock.Mock(autospec=ssh.SSH)
             ssh_mock.execute = \
                  mock.Mock(return_value=(0, {}, ""))
             ssh.return_value = ssh_mock
             ovs_obj = ovsdpdk.Ovsdpdk()
             ovs_obj.connection = ssh_mock
             ovs_obj.ovs = OVS
             self.assertIsNone(ovs_obj.start_ovs_serverswitch())

    def test_setup_ovs_bridge(self):
          with mock.patch("yardstick.ssh.SSH") as ssh:
              ssh_mock = mock.Mock(autospec=ssh.SSH)
              ssh_mock.execute = \
                   mock.Mock(return_value=(0, {}, ""))
              ssh.return_value = ssh_mock
              ovs_obj = ovsdpdk.Ovsdpdk()
              ovs_obj.connection = ssh_mock
              ovs_obj.ovs = OVS
              self.assertIsNone(ovs_obj.setup_ovs_bridge())

    def test_add_oflows(self):
          with mock.patch("yardstick.ssh.SSH") as ssh:
              ssh_mock = mock.Mock(autospec=ssh.SSH)
              ssh_mock.execute = \
                   mock.Mock(return_value=(0, {}, ""))
              ssh.return_value = ssh_mock
              ovs_obj = ovsdpdk.Ovsdpdk()
              ovs_obj.connection = ssh_mock
              ovs_obj.ovs = OVS
              self.assertIsNone(ovs_obj.add_oflows())

    def test_setup_ovs_context_vm_already_present(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.connection = ssh_mock
            ovs_obj.ovs = OVS
            mock_ovs = mock.Mock()
            ssh_mock.put = mock.Mock()
            ovs_obj.check_output = mock.Mock(return_value=(0, "vm1"))
            with mock.patch("yardstick.benchmark.contexts.standalone.ovsdpdk.time"):
                self.assertIsNone(ovs_obj.setup_ovs_context(PCIS, NIC_DETAILS, DRIVER))

    @mock.patch(
        'yardstick.benchmark.contexts.standalone.ovsdpdk',
        return_value="Domain vm1 created from /tmp/vm_ovs.xml")
    def test_is_vm_created(self, NIC_INPUT):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.put = \
            mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            mock_ovs = mock.Mock()
            ret_create = mock.Mock()
            pcis = NIC_DETAILS['pci']
            driver = NIC_DETAILS['phy_driver']
            self.assertIsNotNone(
            mock_ovs.ovs_obj.setup_ovs_context(
                pcis,
                NIC_DETAILS,
                driver))

    def test_check_output(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            cmd = "command"
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.connection = ssh_mock
            self.assertIsNotNone(ovs_obj.check_output(cmd, None))

    def test_split_cpu_list_available(self):
        with mock.patch("itertools.chain") as iter1:
            iter1 = mock.Mock()
            print("{0}".format(iter1))
            ovs_obj = ovsdpdk.Ovsdpdk()
            self.assertIsNotNone(ovs_obj.split_cpu_list('0,5'))

    def test_split_cpu_list_null(self):
        with mock.patch("itertools.chain") as iter1:
            iter1 = mock.Mock()
            print("{0}".format(iter1))
            ovs_obj = ovsdpdk.Ovsdpdk()
            self.assertEqual(ovs_obj.split_cpu_list([]), [])

    def test_destroy_vm_successful(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.connection = ssh_mock
            ovs_obj.ovs = OVS
            ovs_obj.check_output = mock.Mock(return_value=(0, "vm1"))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "0 i40e"))
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "0 i40e"))
            self.assertIsNone(ovs_obj.destroy_vm())

    def test_destroy_vm_unsuccessful(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            ovs_obj = ovsdpdk.Ovsdpdk()
            ovs_obj.connection = ssh_mock
            ovs_obj.ovs = OVS
            ovs_obj.check_output = mock.Mock(return_value=(1, {}))
            self.assertIsNone(ovs_obj.destroy_vm())

    def test_read_from_file(self):
        CORRECT_FILE_PATH = self._get_file_abspath(self.NODES_SAMPLE_PASSWORD)
        ovs_obj = ovsdpdk.Ovsdpdk()
        self.assertIsNotNone(ovs_obj.read_from_file(CORRECT_FILE_PATH))

    def test_write_to_file(self):
        ovs_obj = ovsdpdk.Ovsdpdk()
        self.assertIsNone(ovs_obj.write_to_file(SAMPLE_FILE, "some content"))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

if __name__ == '__main__':
    unittest.main()
