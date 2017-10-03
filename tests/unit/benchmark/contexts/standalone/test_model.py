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

# Unittest for yardstick.benchmark.contexts.standalone.model


from __future__ import absolute_import
import os
import unittest
import mock

from yardstick import ssh
from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services.utils import PciAddress


class StandaloneModelTestCase(unittest.TestCase):

    NODE_SAMPLE = "nodes_sample.yaml"
    NODE_SRIOV_SAMPLE = "nodes_sriov_sample.yaml"

    NETWORKS = {
        'mgmt': {
            'cidr': '152.16.100.10/24',
        },
        'private_0': {
            'phy_port': "0000:05:00.0",
            'vpci': "0000:00:07.0",
            'cidr': '152.16.100.10/24',
            'gateway_ip': '152.16.100.20',
        },
        'public_0': {
            'phy_port': "0000:05:00.1",
            'vpci': "0000:00:08.0",
            'cidr': '152.16.40.10/24',
            'gateway_ip': '152.16.100.20',
        }
    }

    NETWORKS_WITH_DRIVER = {
        'mgmt': {
            'cidr': '152.16.100.10/24'
        },
        'private_0': {
            'phy_port': "0000:05:00.0",
            'vpci': "0000:00:07.0",
            'driver': 'i40e',
            'mac': '',
            'cidr': '152.16.100.10/24',
            'gateway_ip': '152.16.100.20'
        },
        'public_0': {
            'phy_port': "0000:05:00.1",
            'vpci': "0000:00:08.0",
            'driver': 'i40e',
            'mac': '',
            'cidr': '152.16.40.10/24',
            'gateway_ip': '152.16.100.20',
        }
    }

    def test_check_if_vm_exists_and_delete(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        model.check_if_vm_exists_and_delete("vm_0", ssh_mock)

    def test_virsh_create_vm(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        model.virsh_create_vm(ssh_mock, "vm_0")

    def test_virsh_destroy_vm(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        model.virsh_destroy_vm("vm_0", ssh_mock)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.ET')
    def test_add_interface_address(self, mock_et):
        pci_address = PciAddress.parse_address("0000:00:04.0", multi_line=True)

        result = model.add_interface_address("<interface/>", pci_address)
        self.assertIsNotNone(result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.add_interface_address')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.ET')
    def test_add_ovs_interfaces(self, mock_et, mock_add_interface_address):
        mac_addr = "00:00:00:00:00:01"
        model.add_ovs_interface("/usr/local", 0, "0000:00:04.0", mac_addr, "xml")

    @mock.patch('yardstick.benchmark.contexts.standalone.model.add_interface_address')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.ET')
    def test_add_sriov_interfaces(self, mock_et, mock_add_interface_address):
        mac_addr = "00:00:00:00:00:01"
        model.add_sriov_interfaces("0000:00:05.0", "0000:00:04.0", mac_addr, "xml")

    def test_create_snapshot_qemu(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        expected = "/var/lib/libvirt/images/0.qcow2"
        result = model.create_snapshot_qemu(ssh_mock, "0", "ubuntu.img")
        self.assertEqual(result, expected)

    @mock.patch("yardstick.benchmark.contexts.standalone.model.create_snapshot_qemu")
    @mock.patch('yardstick.benchmark.contexts.standalone.model.open')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.write_file')
    def test_build_vm_xml(self, mock_open, mock_write_file, mock_create_snapshot_qemu):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""
        mock_create_snapshot_qemu.return_value = "0.img"

        expected = 4
        result = model.build_vm_xml(ssh_mock, {}, "test", "vm_0", 0)
        self.assertEqual(result[0], expected)

    def test_split_cpu_list(self):
        cpu_input = "1,5-7,3,11-14,8-9"
        expected = [1, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14]
        result = model.split_cpu_list(cpu_input)
        self.assertEqual(result, expected)

    def test_get_numa_nodes(self):
        result = model.get_numa_nodes()
        self.assertIsNotNone(result)

    def test_update_interrupts_hugepages_perf(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        model.update_interrupts_hugepages_perf(ssh_mock)

    @mock.patch("yardstick.benchmark.contexts.standalone.model.get_numa_nodes")
    @mock.patch("yardstick.benchmark.contexts.standalone.model.update_interrupts_hugepages_perf")
    def test_pin_vcpu_for_perf(self, mock_update_interrupts_hugepages_perf, mock_get_numa_nodes):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""
        mock_get_numa_nodes.return_value = {'1': [18, 19, 20, 21], '0': [0, 1, 2, 3]}

        model.pin_vcpu_for_perf(ssh_mock, "vm_0", 4)

    def test_install_req_libs(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "a", ""

        model.install_req_libs(ssh_mock)

    def test_get_kernel_module(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "i40e", ""

        result = model.get_kernel_module(ssh_mock, "05:00.0", None)
        self.assertEqual(result, "i40e")

    @mock.patch('yardstick.benchmark.contexts.standalone.model.get_kernel_module')
    def test_populate_nic_details(self, mock_get_kernel_module):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "i40e ixgbe", ""
        mock_get_kernel_module.return_value = "i40e"

        model.populate_nic_details(ssh_mock, self.NETWORKS, "dpdk-devbind.py")

    def test_get_virtual_devices(self):
        pattern = "PCI_SLOT_NAME=0000:05:00.0"
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, pattern, ""

        model.get_virtual_devices(ssh_mock, "0000:00:05.0")

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test_parse_pod_file(self):
        with self.assertRaises(IOError):
            model.parse_pod_file(self._get_file_abspath("dummy"))

        with self.assertRaises(RuntimeError):
            model.parse_pod_file(self._get_file_abspath(self.NODE_SAMPLE))

        file_path = self._get_file_abspath(self.NODE_SRIOV_SAMPLE)
        self.assertIsNotNone(model.parse_pod_file(file_path))

    @mock.patch('yardstick.benchmark.contexts.standalone.model.ssh')
    def test_find_mgmt_ip(self, mock_ssh):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "10.20.30.40 00:00:00:00:00:01", ""
        mock_ssh.from_node.return_value = ssh_mock

        result = model.find_mgmt_ip(ssh_mock, "00:00:00:00:00:01", "10.1.1.1/24", {})
        self.assertIsNotNone(result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.time')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.ssh')
    def test_find_mgmt_ip_negative(self, mock_ssh, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "", ""
        mock_ssh.from_node.return_value = ssh_mock

        model.find_mgmt_ip(ssh_mock, "99", "10.1.1.1/24", {})

    def test_build_vnf_interfaces(self):
        vnf = {
            "network_ports": {
                'mgmt': {'cidr': '152.16.100.10/24'},
                'xe0': ['private_0'],
                'xe1': ['public_0'],
            }
        }
        status = model.build_vnf_interfaces(vnf, self.NETWORKS_WITH_DRIVER)
        self.assertIsNotNone(status)

    def test_generate_vnf_instance(self):
        vnf = {
            "network_ports": {
                'mgmt': {'cidr': '152.16.100.10/24'},
                'xe0': ['private_0'],
                'xe1': ['public_0'],
            }
        }
        status = model.generate_vnf_instance({}, self.NETWORKS_WITH_DRIVER, "1.1.1.1/24",
                                             'vm_0', vnf, '00:00:00:00:00:01')
        self.assertIsNotNone(status)


class OvsDeployTestCase(unittest.TestCase):

    NETWORKS = {
        'mgmt': {
            'cidr': '152.16.100.10/24',
        },
        'private_0': {
            'phy_port': "0000:05:00.0",
            'vpci': "0000:00:07.0",
            'driver': 'i40e',
            'mac': '',
            'cidr': '152.16.100.10/24',
            'gateway_ip': '152.16.100.20',
        },
        'public_0': {
            'phy_port': "0000:05:00.1",
            'vpci': "0000:00:08.0",
            'driver': 'i40e',
            'mac': '',
            'cidr': '152.16.40.10/24',
            'gateway_ip': '152.16.100.20',
        }
    }

    def setUp(self):
        self.ovs_deploy = model.OvsDeploy(mock.Mock(), '/tmp/dpdk-devbind.py', {})

    def test___init__(self):
        self.assertIsNotNone(self.ovs_deploy.connection)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_prerequisite(self, mock_os):
        self.ovs_deploy.prerequisite()

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_prerequisite(self, mock_os):
        self.ovs_deploy.connection.execute.return_value = 1, "1.2.3.4 00:00:00:00:00:01", ""
        self.ovs_deploy.prerequisite = mock.Mock()

        self.ovs_deploy.ovs_deploy()
