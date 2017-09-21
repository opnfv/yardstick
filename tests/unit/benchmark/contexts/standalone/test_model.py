#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015-2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.node

from __future__ import absolute_import
import os
import unittest
import errno
import mock

from yardstick.common import constants as consts
from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services.utils import PciAddress


class ModelLibvirtTestCase(unittest.TestCase):

    def setUp(self):
        self.libvirt = model.Libvirt()

    def test___init__(self):
        self.assertIsNotNone(self.libvirt)

    def test_check_if_vm_exists_and_delete(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        result = self.libvirt.check_if_vm_exists_and_delete("vm_0", ssh_mock)
        self.assertIsNone(result)

    def test_virsh_create_vm(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        result = self.libvirt.virsh_create_vm(ssh_mock, "vm_0")
        self.assertIsNone(result)

    def test_virsh_destroy_vm(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        result = self.libvirt.virsh_destroy_vm("vm_0", ssh_mock)
        self.assertIsNone(result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.ET')
    def test_add_interface_address(self, mock_et):
        pci_address = PciAddress.parse_address("0000:00:04.0", multi_line=True)
        result = self.libvirt.add_interface_address("<interface/>", pci_address)
        self.assertIsNotNone(result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.ET')
    def test_add_ovs_interfaces(self, mock_et):
        pci_address = PciAddress.parse_address("0000:00:04.0", multi_line=True)
        self.libvirt.add_interface_address = mock.Mock(return_value="")
        result = self.libvirt.add_ovs_interface("/usr/local", 0, "0000:00:04.0",
                                                "00:00:00:00:00:01", "xml")
        self.assertIsNone(result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.ET')
    def test_add_sriov_interfaces(self, mock_et):
        pci_address = PciAddress.parse_address("0000:00:04.0", multi_line=True)
        self.libvirt.add_interface_address = mock.Mock(return_value="")
        result = self.libvirt.add_sriov_interfaces("0000:00:05.0", "0000:00:04.0",
                                                   "00:00:00:00:00:01", "xml")
        self.assertIsNone(result)

    def test_create_snapshot_qemu(self):
        result = "/var/lib/libvirt/images/0.qcow2"
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        image = self.libvirt.create_snapshot_qemu(ssh_mock, "0", "ubuntu.img")
        self.assertEqual(image, result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.open')
    def test_build_vm_xml(self, mock_open):
        result = [4]
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.libvirt.create_snapshot_qemu = mock.Mock(return_value="0.img")
        status = self.libvirt.build_vm_xml(ssh_mock, {}, "test", "vm_0", 0)
        self.assertEqual(status[0], result[0])

    def test_split_cpu_list(self):
        result = self.libvirt.split_cpu_list("1,2,3")
        self.assertEqual(result, [1, 2, 3])

    def test_get_numa_nodes(self):
        result = self.libvirt.get_numa_nodes()
        self.assertIsNotNone(result)

    def test_update_interrupts_hugepages_perf(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        status = self.libvirt.update_interrupts_hugepages_perf(ssh_mock)
        self.assertIsNone(status)

    def test_pin_vcpu_for_perf(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        self.libvirt.update_interrupts_hugepages_perf = mock.Mock()
        self.libvirt.get_numa_nodes = mock.Mock(return_value={'1': [18, 19, 20, 21], '0': [0, 1, 2, 3]})
        status = self.libvirt.pin_vcpu_for_perf(ssh_mock, "vm_0", 4)
        self.assertIsNone(status)

class HelperClassTestCase(unittest.TestCase):

    NODE_SAMPLE = "nodes_sample.yaml"
    NODE_SRIOV_SAMPLE = "nodes_sriov_sample.yaml"

    NETWORKS = {
        'mgmt': {'cidr': '152.16.100.10/24'},
        'private_0': {
         'phy_port': "0000:05:00.0",
         'vpci': "0000:00:07.0",
         'cidr': '152.16.100.10/24',
         'gateway_ip': '152.16.100.20'},
        'public_0': {
         'phy_port': "0000:05:00.1",
         'vpci': "0000:00:08.0",
         'cidr': '152.16.40.10/24',
         'gateway_ip': '152.16.100.20'}
    }

    def setUp(self):
        self.helper = model.HelperClass()

    def test___init__(self):
        self.assertIsNone(self.helper.file_path)

    def test_install_req_libs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "a", ""))
            ssh.return_value = ssh_mock
        status = self.helper.install_req_libs(ssh_mock)
        self.assertIsNone(status)

    def test_get_kernel_module(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "i40e", ""))
            ssh.return_value = ssh_mock
        status = self.helper.get_kernel_module(ssh_mock, "05:00.0", None)
        self.assertEqual(status, "i40e")

    def test_get_nic_details(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "i40e ixgbe", ""))
            ssh.return_value = ssh_mock
        self.helper.get_kernel_module = mock.Mock(return_value="i40e")
        status = self.helper.get_nic_details(ssh_mock, self.NETWORKS, "dpdk-devbind.py")
        self.assertIsNotNone(status)

    def test_get_virtual_devices(self):
        pattern = "PCI_SLOT_NAME=0000:05:00.0"
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                    mock.Mock(return_value=(1, pattern, ""))
            ssh.return_value = ssh_mock
        status = self.helper.get_virtual_devices(ssh_mock, "0000:00:05.0")
        self.assertIsNotNone(status)

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test_read_config_file(self):
        self.helper.file_path = self._get_file_abspath(self.NODE_SAMPLE)
        status = self.helper.read_config_file()
        self.assertIsNotNone(status)

    def test_parse_pod_file(self):
        self.helper.file_path = self._get_file_abspath("dummy")
        self.assertRaises(IOError, self.helper.parse_pod_file, self.helper.file_path)

        self.helper.file_path = self._get_file_abspath(self.NODE_SAMPLE)
        self.assertRaises(TypeError, self.helper.parse_pod_file, self.helper.file_path)

        self.helper.file_path = self._get_file_abspath(self.NODE_SRIOV_SAMPLE)
        self.assertIsNotNone(self.helper.parse_pod_file(self.helper.file_path))

    def test_get_mac_address(self):
        status = model.HelperClass.get_mac_address()
        self.assertIsNotNone(status)

    @mock.patch('yardstick.ssh.SSH')
    def test_get_mgmt_ip(self, mock_ssh):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                    mock.Mock(return_value=(1, "1.2.3.4 00:00:00:00:00:01", ""))
            ssh.return_value = ssh_mock
        status = self.helper.get_mgmt_ip(ssh_mock, "00:00:00:00:00:01", "1.1.1.1/24", {})
        self.assertIsNotNone(status)

    @mock.patch('yardstick.ssh.SSH')
    def test_get_mgmt_ip_no(self, mock_ssh):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                    mock.Mock(return_value=(1, "", ""))
            ssh.return_value = ssh_mock

        model.WAIT_FOR_BOOT = 0
        status = self.helper.get_mgmt_ip(ssh_mock, "99", "1.1.1.1/24", {})
        self.assertIsNone(status)

class ServerTestCase(unittest.TestCase):

    NETWORKS = {
        'mgmt': {'cidr': '152.16.100.10/24'},
        'private_0': {
         'phy_port': "0000:05:00.0",
         'vpci': "0000:00:07.0",
         'driver': 'i40e',
         'mac': '',
         'cidr': '152.16.100.10/24',
         'gateway_ip': '152.16.100.20'},
        'public_0': {
         'phy_port': "0000:05:00.1",
         'vpci': "0000:00:08.0",
         'driver': 'i40e',
         'mac': '',
         'cidr': '152.16.40.10/24',
         'gateway_ip': '152.16.100.20'}
    }
    def setUp(self):
        self.server = model.Server()

    def test___init__(self):
        self.assertIsNotNone(self.server)

    def test_build_vnf_interfaces(self):
        vnf = {
            "network_ports": {
                'mgmt': {'cidr': '152.16.100.10/24'},
                'xe0': ['private_0'],    
                'xe1': ['public_0'],    
            }
        }
        status = model.Server.build_vnf_interfaces(vnf, self.NETWORKS)
        self.assertIsNotNone(status)

    def test_generate_vnf_instance(self):
        vnf = {
            "network_ports": {
                'mgmt': {'cidr': '152.16.100.10/24'},
                'xe0': ['private_0'],    
                'xe1': ['public_0'],    
            }
        }
        status = self.server.generate_vnf_instance({}, self.NETWORKS, "1.1.1.1/24", 'vm_0', vnf, '00:00:00:00:00:01')
        self.assertIsNotNone(status)

class OvsDeployTestCase(unittest.TestCase):

    NETWORKS = {
        'mgmt': {'cidr': '152.16.100.10/24'},
        'private_0': {
         'phy_port': "0000:05:00.0",
         'vpci': "0000:00:07.0",
         'driver': 'i40e',
         'mac': '',
         'cidr': '152.16.100.10/24',
         'gateway_ip': '152.16.100.20'},
        'public_0': {
         'phy_port': "0000:05:00.1",
         'vpci': "0000:00:08.0",
         'driver': 'i40e',
         'mac': '',
         'cidr': '152.16.40.10/24',
         'gateway_ip': '152.16.100.20'}
    }
    @mock.patch('yardstick.ssh.SSH')
    def setUp(self, mock_ssh):
        self.ovs_deploy = model.OvsDeploy(mock_ssh, '/tmp/dpdk-devbind.py', {})

    def test___init__(self):
        self.assertIsNotNone(self.ovs_deploy.connection)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_prerequisite(self, mock_ssh):
        self.ovs_deploy.helper = mock.Mock()
        self.assertIsNone(self.ovs_deploy.prerequisite())

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_prerequisite(self, mock_ssh):
        self.ovs_deploy.helper = mock.Mock()
        self.ovs_deploy.connection.execute = \
                    mock.Mock(return_value=(1, "1.2.3.4 00:00:00:00:00:01", ""))
        self.ovs_deploy.prerequisite = mock.Mock()
        self.assertIsNone(self.ovs_deploy.ovs_deploy())
