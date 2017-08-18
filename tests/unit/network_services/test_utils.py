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

# Unittest for yardstick.network_services.utils

from __future__ import absolute_import

import os
import unittest
import mock

from yardstick import ssh
from yardstick.network_services import utils


class TestPciAddress(unittest.TestCase):

    def test___init__negative(self):
        with self.assertRaises(ValueError):
            utils.PciAddress('not an address')

        with self.assertRaises(ValueError):
            utils.PciAddress('0123.45.67.8')

    def test___repr__(self):
        base_value = '0f1e:2D:C3.b'
        pci_address = utils.PciAddress(base_value)
        self.assertEqual(repr(pci_address), base_value)

    def test_properties(self):
        base_value = '0f1e:2D:C3.b'
        expected_values = ['0f1e', '2D', 'C3', 'b']
        pci_address = utils.PciAddress(base_value)
        self.assertEqual(pci_address.values(), expected_values)
        self.assertEqual(pci_address.domain, expected_values[0])
        self.assertEqual(pci_address.bus, expected_values[1])
        self.assertEqual(pci_address.function, expected_values[2])
        self.assertEqual(pci_address.slot, expected_values[3])


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
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, self.DPDK_PATH, ""
        tool_path = utils.provision_tool(ssh_mock, self.DPDK_PATH)
        self.assertEqual(tool_path, self.DPDK_PATH)

    def test_provision_tool_not_found(self):
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 1, self.DPDK_PATH, ""
        tool_path = utils.provision_tool(ssh_mock, self.DPDK_PATH)
        self.assertEqual(tool_path, self.DPDK_PATH)

    @mock.patch('yardstick.network_services.utils.get_nsb_option')
    def test_provision_tool_file_no_file_path(self, mock_get_nsb_option):
        mock_get_nsb_option.return_value = '/mock_path'
        ssh_mock = mock.Mock(autospec=ssh.SSH)
        ssh_mock.execute.return_value = 0, self.DPDK_PATH, ""
        tool_path = utils.provision_tool(ssh_mock, None, tool_file='tool_file.sh')
        self.assertEqual(tool_path, '/mock_path/tool_file.sh')
