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
import itertools
import os
import unittest
import mock

from xml.etree import ElementTree
from yardstick import ssh
from yardstick.benchmark.contexts.standalone import model
from yardstick.network_services.helpers.dpdkbindnic_helper import DpdkBindHelper

from yardstick.network_services import utils


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

    NODES_SAMPLE = [
        {
            'name': 'node1',
            'mac': "DE:AD:BE:EF:DE:AD",
        },
    ]

    SERVERS_SAMPLE = {
        'node1': {
            'network_ports': {
                'mgmt': {
                    'cidr': '1.1.1.1/24',
                },
            },
        },
    }

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
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        # NOTE(ralonsoh): this test doesn't cover function execution.
        model.check_if_vm_exists_and_delete("vm_0", ssh_mock)

    def test_virsh_create_vm(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        # NOTE(ralonsoh): this test doesn't cover function execution.
        model.virsh_create_vm(ssh_mock, "vm_0")

    def test_virsh_create_vm_failure(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "a", ""

        with self.assertRaises(model.StandaloneContextException):
            model.virsh_create_vm(ssh_mock, "vm_0")

    def test_virsh_destroy_vm(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        # NOTE(ralonsoh): this test doesn't cover function execution.
        model.virsh_destroy_vm("vm_0", ssh_mock)

    def test_add_interface_address(self):
        xml = ElementTree.ElementTree(
            element=ElementTree.fromstring(XML_SAMPLE_INTERFACE))
        interface = xml.find('devices').find('interface')
        result = model._add_interface_address(interface, self.pci_address)
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
            model.add_ovs_interface(
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
            model.add_sriov_interfaces(
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
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        expected = "/var/lib/libvirt/images/0.qcow2"
        result = model.create_snapshot_qemu(ssh_mock, "0", "ubuntu.img")
        self.assertEqual(result, expected)

    @mock.patch("yardstick.benchmark.contexts.standalone.model.pin_vcpu_for_perf")
    @mock.patch('yardstick.benchmark.contexts.standalone.model.open')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.write_file')
    @mock.patch("yardstick.benchmark.contexts.standalone.model.create_snapshot_qemu")
    def test_build_vm_xml(self, mock_create_snapshot_qemu, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""
        mock_create_snapshot_qemu.return_value = "0.img"

        model.build_vm_xml(ssh_mock, {}, "test", "vm_0", 0)

    def test_update_interrupts_hugepages_perf(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""

        model.update_interrupts_hugepages_perf(ssh_mock)

    @mock.patch("yardstick.benchmark.contexts.standalone.model.CpuSysCores")
    @mock.patch("yardstick.benchmark.contexts.standalone.model.update_interrupts_hugepages_perf")
    def test_pin_vcpu_for_perf(self, *_):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, "a", ""
        status = model.pin_vcpu_for_perf(ssh_mock)
        self.assertIsNotNone(status)

        model.pin_vcpu_for_perf(ssh_mock)

    def test_install_req_libs(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "a", ""

        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.install_req_libs(ssh_mock, extra_pkgs=['pkg1', 'pkg2'])

    def test_get_kernel_module(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "i40e", ""

        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        result = model.get_kernel_module(ssh_mock, "05:00.0", None)
        self.assertEqual(result, "i40e")

    @mock.patch('yardstick.benchmark.contexts.standalone.model.get_kernel_module')
    def test_populate_nic_details(self, mock_get_kernel_module):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, "i40e ixgbe", ""
        mock_get_kernel_module.return_value = "i40e"

        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        model.populate_nic_details(ssh_mock, self.NETWORKS, mock.Mock(autospec=DpdkBindHelper))

    def test_get_virtual_devices(self):
        pattern = "PCI_SLOT_NAME=0000:05:00.0"
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, pattern, ""

        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
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

        # NOTE(ralonsoh): this test doesn't cover function execution. This test
        # should also check mocked function calls.
        result = model.find_mgmt_ip(ssh_mock, "00:00:00:00:00:01", "10.1.1.1/24", {})
        self.assertIsNotNone(result)

    @mock.patch('yardstick.benchmark.contexts.standalone.model.time')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.ssh')
    def test_find_mgmt_ip_negative(self, mock_ssh, *_):
        sample_cidr = '1.1.1.0/24'
        sample_ip = '1.1.1.1'
        sample_mac = '00:10:20:30:0A:0B'

        successful_fping_answer = (0, "", "")
        address_not_found_answer = (1, "", "")
        address_found_answer = (0, "{} dev eth0 lladdr {} STALE".format(sample_ip, sample_mac), "")

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.side_effect = [
            successful_fping_answer, address_not_found_answer,
            successful_fping_answer, address_not_found_answer,
            successful_fping_answer, address_found_answer,
        ]
        mock_ssh.from_node.return_value = ssh_mock

        self.assertEquals(sample_ip,
                          model.find_mgmt_ip(ssh_mock, sample_mac, sample_cidr, {}))

    @mock.patch('yardstick.benchmark.contexts.standalone.model.time')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.ssh')
    def test_find_mgmt_ip_notfound(self, mock_ssh, *_):
        sample_cidr = '1.1.1.0/24'
        sample_mac = '00:10:20:30:0A:0B'

        successful_fping_answer = (0, "", "")
        address_not_found_answer = (1, "", "")

        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.side_effect = itertools.cycle(
            [
                successful_fping_answer,
                address_not_found_answer,
            ]
        )
        mock_ssh.from_node.return_value = ssh_mock

        with self.assertRaises(RuntimeError):
            model.find_mgmt_ip(ssh_mock, sample_mac, sample_cidr, {})

    @mock.patch('yardstick.benchmark.contexts.standalone.model.find_mgmt_ip')
    def test_wait_for_vnfs_to_start(self, _):
        connection = mock.Mock()
        model.wait_for_vnfs_to_start(connection, self.SERVERS_SAMPLE, self.NODES_SAMPLE)

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

    @mock.patch('yardstick.benchmark.contexts.standalone.model.install_req_libs')
    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_prerequisite(self, *_):
        self.ovs_deploy.prerequisite()

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_ovs_deploy(self, _):
        self.ovs_deploy.connection.execute.return_value = 0, "some output", ""
        self.ovs_deploy.prerequisite = mock.Mock()

        self.ovs_deploy.ovs_deploy()

    @mock.patch('yardstick.benchmark.contexts.standalone.model.os')
    def test_ovs_deploy_with_failure(self, _):
        self.ovs_deploy.connection.execute.return_value = 1, "some output", "some error output"
        self.ovs_deploy.prerequisite = mock.Mock()

        with self.assertRaises(ssh.SSHCommandError):
            self.ovs_deploy.ovs_deploy()
