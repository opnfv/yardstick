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
