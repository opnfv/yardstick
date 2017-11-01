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
import copy
import os
import unittest
import mock

from xml.etree import ElementTree

from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services import utils
from yardstick.network_services.helpers import cpu


XML_SAMPLE = """<?xml version="1.0"?>
<domain type="kvm">
    <devices>
    </devices>
</domain>
"""

XML_SAMPLE_INTERFACE = """<?xml version="1.0"?>
<domain type="kvm">
    <devices>
        <interface>
        </interface>
    </devices>
</domain>
"""

class ModelLibvirtTestCase(unittest.TestCase):

    def setUp(self):
        self.xml = ElementTree.ElementTree(
            element=ElementTree.fromstring(XML_SAMPLE))
        self.pci_address_str = '0001:04:03.2'
        self.pci_address = utils.PciAddress(self.pci_address_str)
        self.mac = '00:00:00:00:00:01'
        self._mock_write_xml = mock.patch.object(ElementTree.ElementTree,
                                                 'write')
        self.mock_write_xml = self._mock_write_xml.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_write_xml.stop()

    def test_check_if_vm_exists_and_delete(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution.
        model.Libvirt.check_if_vm_exists_and_delete("vm_0", ssh_mock)

    def test_virsh_create_vm(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution.
        model.Libvirt.virsh_create_vm(ssh_mock, "vm_0")

    def test_virsh_destroy_vm(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution.
        model.Libvirt.virsh_destroy_vm("vm_0", ssh_mock)

    def test_add_interface_address(self):
        xml = ElementTree.ElementTree(
            element=ElementTree.fromstring(XML_SAMPLE_INTERFACE))
        interface = xml.find('devices').find('interface')
        result = model.Libvirt._add_interface_address(interface, self.pci_address)
        self.assertEqual('pci', result.get('type'))
        self.assertEqual('0x{}'.format(self.pci_address.domain),
                         result.get('domain'))
        self.assertEqual('0x{}'.format(self.pci_address.bus),
                         result.get('bus'))
        self.assertEqual('0x{}'.format(self.pci_address.slot),
                         result.get('slot'))
        self.assertEqual('0x{}'.format(self.pci_address.function),
                         result.get('function'))

    def test_add_ovs_interfaces(self):
        xml_input = mock.Mock()
        with mock.patch.object(ElementTree, 'parse', return_value=self.xml) \
                as mock_parse:
            xml = copy.deepcopy(self.xml)
            mock_parse.return_value = xml
            model.Libvirt.add_ovs_interface(
                '/usr/local', 0, self.pci_address_str, self.mac, xml_input)
            mock_parse.assert_called_once_with(xml_input)
            self.mock_write_xml.assert_called_once_with(xml_input)
            interface = xml.find('devices').find('interface')
            self.assertEqual('vhostuser', interface.get('type'))
            mac = interface.find('mac')
            self.assertEqual(self.mac, mac.get('address'))
            source = interface.find('source')
            self.assertEqual('unix', source.get('type'))
            self.assertEqual('/usr/local/var/run/openvswitch/dpdkvhostuser0',
                             source.get('path'))
            self.assertEqual('client', source.get('mode'))
            _model = interface.find('model')
            self.assertEqual('virtio', _model.get('type'))
            driver = interface.find('driver')
            self.assertEqual('4', driver.get('queues'))
            host = driver.find('host')
            self.assertEqual('off', host.get('mrg_rxbuf'))
            self.assertIsNotNone(interface.find('address'))

    def test_add_sriov_interfaces(self):
        xml_input = mock.Mock()
        with mock.patch.object(ElementTree, 'parse', return_value=self.xml) \
                as mock_parse:
            xml = copy.deepcopy(self.xml)
            mock_parse.return_value = xml
            vf_pci = '0001:05:04.2'
            model.Libvirt.add_sriov_interfaces(
                self.pci_address_str, vf_pci, self.mac, xml_input)
            mock_parse.assert_called_once_with(xml_input)
            self.mock_write_xml.assert_called_once_with(xml_input)
            interface = xml.find('devices').find('interface')
            self.assertEqual('yes', interface.get('managed'))
            self.assertEqual('hostdev', interface.get('type'))
            mac = interface.find('mac')
            self.assertEqual(self.mac, mac.get('address'))
            source = interface.find('source')
            self.assertIsNotNone(source.find('address'))
            self.assertIsNotNone(interface.find('address'))

    def test_create_snapshot_qemu(self):
        result = "/var/lib/libvirt/images/0.qcow2"
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        image = model.Libvirt.create_snapshot_qemu(ssh_mock, "0", "ubuntu.img")
        self.assertEqual(image, result)

    @mock.patch.object(model.Libvirt, 'pin_vcpu_for_perf')
    @mock.patch.object(model.Libvirt, 'create_snapshot_qemu')
    def test_build_vm_xml(self, mock_create_snapshot_qemu,
                          *args):
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        result = [4]
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        mock_create_snapshot_qemu.return_value = "0.img"

        status = model.Libvirt.build_vm_xml(ssh_mock, {}, "test", "vm_0", 0)
        self.assertEqual(status[0], result[0])

    def test_update_interrupts_hugepages_perf(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "a", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.Libvirt.update_interrupts_hugepages_perf(ssh_mock)

    @mock.patch.object(cpu.CpuSysCores, 'get_core_socket')
    def test_pin_vcpu_for_perf(self, mock_get_core_socket):
        mock_get_core_socket.return_value = {
            'cores_per_socket': 1,
            'thread_per_core': 1,
            '0': [1, 2]
        }
        # NOTE(ralonsoh): this test doesn't cover function execution. This
        # function needs more tests.
        model.Libvirt.pin_vcpu_for_perf(mock.Mock())


class StandaloneContextHelperTestCase(unittest.TestCase):

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
        self.helper = model.StandaloneContextHelper()

    def test___init__(self):
        self.assertIsNone(self.helper.file_path)

    def test_install_req_libs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "a", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.StandaloneContextHelper.install_req_libs(ssh_mock)

    def test_get_kernel_module(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "i40e", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.StandaloneContextHelper.get_kernel_module(
            ssh_mock, "05:00.0", None)

    @mock.patch.object(model.StandaloneContextHelper, 'get_kernel_module')
    def test_get_nic_details(self, mock_get_kernel_module):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "i40e ixgbe", ""))
            ssh.return_value = ssh_mock
        mock_get_kernel_module.return_value = "i40e"
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.StandaloneContextHelper.get_nic_details(
            ssh_mock, self.NETWORKS, 'dpdk-devbind.py')

    def test_get_virtual_devices(self):
        pattern = "PCI_SLOT_NAME=0000:05:00.0"
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                    mock.Mock(return_value=(1, pattern, ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.StandaloneContextHelper.get_virtual_devices(
            ssh_mock, '0000:00:05.0')

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
        self.assertRaises(IOError, self.helper.parse_pod_file,
                          self.helper.file_path)

        self.helper.file_path = self._get_file_abspath(self.NODE_SAMPLE)
        self.assertRaises(TypeError, self.helper.parse_pod_file,
                          self.helper.file_path)

        self.helper.file_path = self._get_file_abspath(self.NODE_SRIOV_SAMPLE)
        self.assertIsNotNone(self.helper.parse_pod_file(self.helper.file_path))

    def test_get_mac_address(self):
        status = model.StandaloneContextHelper.get_mac_address()
        self.assertIsNotNone(status)

    @mock.patch('yardstick.ssh.SSH')
    def test_get_mgmt_ip(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(
                return_value=(1, "1.2.3.4 00:00:00:00:00:01", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        status = model.StandaloneContextHelper.get_mgmt_ip(
            ssh_mock, "00:00:00:00:00:01", "1.1.1.1/24", {})
        self.assertIsNotNone(status)

    @mock.patch('yardstick.ssh.SSH')
    def test_get_mgmt_ip_no(self, *args):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                    mock.Mock(return_value=(1, "", ""))
            ssh.return_value = ssh_mock
        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.WAIT_FOR_BOOT = 0
        status = model.StandaloneContextHelper.get_mgmt_ip(
            ssh_mock, "99", "1.1.1.1/24", {})
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
        status = self.server.generate_vnf_instance(
            {}, self.NETWORKS, '1.1.1.1/24', 'vm_0', vnf, '00:00:00:00:00:01')
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
    def test_prerequisite(self, *args):
        # NOTE(ralonsoh): this test should check mocked function calls.
        self.ovs_deploy.helper = mock.Mock()
        self.assertIsNone(self.ovs_deploy.prerequisite())

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_prerequisite_2(self, *args):
        # NOTE(ralonsoh): this test should check mocked function calls. Rename
        # this test properly.
        self.ovs_deploy.helper = mock.Mock()
        self.ovs_deploy.connection.execute = mock.Mock(
            return_value=(1, '1.2.3.4 00:00:00:00:00:01', ''))
        self.ovs_deploy.prerequisite = mock.Mock()
        self.assertIsNone(self.ovs_deploy.ovs_deploy())
