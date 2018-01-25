# Copyright (c) 2018 Intel Corporation
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

import mock
from pip import exceptions as pip_exceptions
from pip.operations import freeze
import unittest

from yardstick.common import packages


class PipExecuteActionTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_pip_main = mock.patch.object(packages, '_pip_main')
        self.mock_pip_main = self._mock_pip_main.start()
        self.mock_pip_main.return_value = 0
        self._mock_freeze = mock.patch.object(freeze, 'freeze')
        self.mock_freeze = self._mock_freeze.start()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_pip_main.stop()
        self._mock_freeze.stop()

    def test_pip_execute_action(self):
        self.assertEqual(0, packages._pip_execute_action('test_package'))

    def test_remove(self):
        self.assertEqual(0, packages._pip_execute_action('test_package',
                                                         action='uninstall'))

    def test_install(self):
        self.assertEqual(0, packages._pip_execute_action(
            'test_package', action='install', target='temp_dir'))

    def test_pip_execute_action_error(self):
        self.mock_pip_main.return_value = 1
        self.assertEqual(1, packages._pip_execute_action('test_package'))

    def test_pip_execute_action_exception(self):
        self.mock_pip_main.side_effect = pip_exceptions.PipError
        self.assertEqual(1, packages._pip_execute_action('test_package'))

    def test_pip_list(self):
        pkg_input = [
            'XStatic-Rickshaw==1.5.0.0',
            'xvfbwrapper==0.2.9',
            '-e git+https://git.opnfv.org/yardstick@50773a24afc02c9652b662ecca'
            '2fc5621ea6097a#egg=yardstick',
            'zope.interface==4.4.3'
        ]
        pkg_dict = {
            'XStatic-Rickshaw': '1.5.0.0',
            'xvfbwrapper': '0.2.9',
            'yardstick': '50773a24afc02c9652b662ecca2fc5621ea6097a',
            'zope.interface': '4.4.3'
        }
        self.mock_freeze.return_value = pkg_input

        pkg_output = packages.pip_list()
        for pkg_name, pkg_version in pkg_output.items():
            self.assertEqual(pkg_dict.get(pkg_name), pkg_version)

    def test_pip_list_single_package(self):
        pkg_input = [
            'XStatic-Rickshaw==1.5.0.0',
            'xvfbwrapper==0.2.9',
            '-e git+https://git.opnfv.org/yardstick@50773a24afc02c9652b662ecca'
            '2fc5621ea6097a#egg=yardstick',
            'zope.interface==4.4.3'
        ]
        self.mock_freeze.return_value = pkg_input

        pkg_output = packages.pip_list(pkg_name='xvfbwrapper')
        self.assertEqual(1, len(pkg_output))
        self.assertEqual(pkg_output.get('xvfbwrapper'), '0.2.9')
