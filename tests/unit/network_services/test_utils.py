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

import os
import unittest
import mock

from yardstick.network_services import utils
from yardstick import ssh


class GetNsbOptionTestCase(unittest.TestCase):
    """Test 'get_nsb_option' method."""

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


class ProvisionToolTestCase(unittest.TestCase):
    """Test 'provision_tool' method."""

    TEST_PATH = '/sample/path'

    def setUp(self):
        self.addCleanup(self._stop_mock)
        self._mock_ssh = mock.patch.object(ssh, 'SSH')
        self.mock_ssh = self._mock_ssh.start()

    def _stop_mock(self):
        self._mock_ssh.stop()

    def test_provision_tool_file_exists(self):
        self.mock_ssh.file_exists.return_value = True
        tool_path = utils.provision_tool(self.mock_ssh, self.TEST_PATH)
        self.assertEqual(self.TEST_PATH, tool_path)

    def test_provision_tool_file_doesnt_exist(self):
        self.mock_ssh.file_exists.return_value = False
        tool_path = utils.provision_tool(self.mock_ssh, self.TEST_PATH)
        self.assertEqual(self.TEST_PATH, tool_path)
        self.mock_ssh.create_directory.assert_called_once_with(
            os.path.dirname(self.TEST_PATH))
        self.mock_ssh.put.assert_called_once_with(tool_path, tool_path)
