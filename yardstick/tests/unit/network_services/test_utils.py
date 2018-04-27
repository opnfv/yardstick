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
#

import os
import unittest
import mock

from yardstick.network_services import utils


class UtilsTestCase(unittest.TestCase):
    """Test all VNF helper methods."""

    DPDK_PATH = os.path.join(utils.NSB_ROOT, "dpdk-devbind.py")

    def setUp(self):
        super(UtilsTestCase, self).setUp()

    def test_get_nsb_options(self):
        result = utils.get_nsb_option("bin_path", None)
        self.assertEqual(result, utils.NSB_ROOT)

    def test_get_nsb_option_is_invalid_key(self):
        result = utils.get_nsb_option("bin", None)
        self.assertEqual(result, None)

    def test_get_nsb_option_default(self):
        default = object()
        result = utils.get_nsb_option("nosuch", default)
        self.assertIs(result, default)

    def test_provision_tool(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, self.DPDK_PATH, ""))
            ssh.return_value = ssh_mock
            tool_path = utils.provision_tool(ssh_mock, self.DPDK_PATH)
            self.assertEqual(tool_path, self.DPDK_PATH)

    def test_provision_tool_no_path(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, self.DPDK_PATH, ""))
            ssh.return_value = ssh_mock
            tool_path = utils.provision_tool(ssh_mock, self.DPDK_PATH)
            self.assertEqual(tool_path, self.DPDK_PATH)


class PciAddressTestCase(unittest.TestCase):

    PCI_ADDRESS_DBSF = '000A:07:03.2'
    PCI_ADDRESS_BSF = '06:02.1'
    PCI_ADDRESS_DBSF_MULTILINE_1 = '0001:08:04.3\nother text\n'
    PCI_ADDRESS_DBSF_MULTILINE_2 = 'first line\n   0001:08:04.3 \nother text\n'
    # Will match and return the first address found.
    PCI_ADDRESS_DBSF_MULTILINE_3 = '  0001:08:04.1  \n  05:03.1 \nother\n'
    PCI_ADDRESS_BSF_MULTILINE_1 = 'first line\n   08:04.3 \n 0002:05:03.1\n'
    BAD_INPUT_1 = 'no address found'
    BAD_INPUT_2 = '001:08:04.1'
    BAD_INPUT_3 = '08:4.1'

    def test_pciaddress_dbsf(self):
        pci_address = utils.PciAddress(PciAddressTestCase.PCI_ADDRESS_DBSF)
        self.assertEqual('000a', pci_address.domain)
        self.assertEqual('07', pci_address.bus)
        self.assertEqual('03', pci_address.slot)
        self.assertEqual('2', pci_address.function)

    def test_pciaddress_bsf(self):
        pci_address = utils.PciAddress(PciAddressTestCase.PCI_ADDRESS_BSF)
        self.assertEqual('0000', pci_address.domain)
        self.assertEqual('06', pci_address.bus)
        self.assertEqual('02', pci_address.slot)
        self.assertEqual('1', pci_address.function)

    def test_pciaddress_dbsf_multiline_1(self):
        pci_address = utils.PciAddress(
            PciAddressTestCase.PCI_ADDRESS_DBSF_MULTILINE_1)
        self.assertEqual('0001', pci_address.domain)
        self.assertEqual('08', pci_address.bus)
        self.assertEqual('04', pci_address.slot)
        self.assertEqual('3', pci_address.function)

    def test_pciaddress_dbsf_multiline_2(self):
        pci_address = utils.PciAddress(
            PciAddressTestCase.PCI_ADDRESS_DBSF_MULTILINE_2)
        self.assertEqual('0001', pci_address.domain)
        self.assertEqual('08', pci_address.bus)
        self.assertEqual('04', pci_address.slot)
        self.assertEqual('3', pci_address.function)

    def test_pciaddress_dbsf_multiline_3(self):
        pci_address = utils.PciAddress(
            PciAddressTestCase.PCI_ADDRESS_DBSF_MULTILINE_3)
        self.assertEqual('0001', pci_address.domain)
        self.assertEqual('08', pci_address.bus)
        self.assertEqual('04', pci_address.slot)
        self.assertEqual('1', pci_address.function)

    def test_pciaddress_bsf_multiline_1(self):
        pci_address = utils.PciAddress(
            PciAddressTestCase.PCI_ADDRESS_BSF_MULTILINE_1)
        self.assertEqual('0000', pci_address.domain)
        self.assertEqual('08', pci_address.bus)
        self.assertEqual('04', pci_address.slot)
        self.assertEqual('3', pci_address.function)

    def test_pciaddress_bad_input_no_address(self):
        with self.assertRaises(ValueError) as exception:
            utils.PciAddress(PciAddressTestCase.BAD_INPUT_1)
        self.assertEqual('Invalid PCI address: {}'.format(
                PciAddressTestCase.BAD_INPUT_1), str(exception.exception))

    def test_pciaddress_bad_input_dbsf_bad_formatted(self):
        # In this test case, the domain has only 3 characters instead of 4.
        pci_address = utils.PciAddress(
            PciAddressTestCase.BAD_INPUT_2)
        self.assertEqual('0000', pci_address.domain)
        self.assertEqual('08', pci_address.bus)
        self.assertEqual('04', pci_address.slot)
        self.assertEqual('1', pci_address.function)

    def test_pciaddress_bad_input_bsf_bad_formatted(self):
        with self.assertRaises(ValueError) as exception:
            utils.PciAddress(PciAddressTestCase.BAD_INPUT_3)
        self.assertEqual('Invalid PCI address: {}'.format(
                PciAddressTestCase.BAD_INPUT_3), str(exception.exception))
