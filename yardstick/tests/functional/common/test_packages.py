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

import os
from os import path
import re

from yardstick.common import packages
from yardstick.tests.functional import base


class PipPackagesTestCase(base.BaseFunctionalTestCase):

    def setUp(self):
        privsep_helper = os.path.join(
            os.getenv('VIRTUAL_ENV'), 'bin', 'privsep-helper')
        self.config(
            helper_command=' '.join(['sudo', '-E', privsep_helper]),
            group='os_vif_privileged')

    def _remove_package(self, package):
        packages.pip_remove(package)

    def _list_packages(self):
        pip_list_regex = re.compile(
            r"(?P<name>[\w\.-]+) \((?P<version>[\w\d_\.\-]+),*.*\)")
        pkg_dict = {}
        for line in os.popen('pip list').read().splitlines():
            match = pip_list_regex.match(line)
            pkg_dict[match.group('name')] = match.group('version')
        return pkg_dict

    def test_install_from_folder(self):
        dirname = path.dirname(__file__)
        package_dir = dirname + '/fake_directory_package'
        package_name = 'yardstick-new-plugin-2'
        self.addCleanup(self._remove_package, package_name)
        self._remove_package(package_name)
        self.assertFalse(any(package_name in _pkg for
                             _pkg in self._list_packages()))

        self.assertEqual(0, packages.pip_install(package_dir))
        self.assertTrue(any(package_name in _pkg for
                            _pkg in self._list_packages()))

    def test_install_from_pip_package(self):
        dirname = path.dirname(__file__)
        package_path = (dirname +
                        '/fake_pip_package/yardstick_new_plugin-1.0.0.tar.gz')
        package_name = 'yardstick-new-plugin'
        self.addCleanup(self._remove_package, package_name)
        self._remove_package(package_name)
        self.assertFalse(any(package_name in _pkg for
                             _pkg in self._list_packages()))

        self.assertEqual(0, packages.pip_install(package_path))
        self.assertTrue(any(package_name in _pkg for
                            _pkg in self._list_packages()))

    # NOTE(ralonsoh): an stable test plugin project is needed in OPNFV git
    # server to execute this test.
    # def test_install_from_url(self):

    def test_pip_freeze(self):
        pkgs_ref = self._list_packages()
        pkgs = packages.pip_list()
        for pkg_name in pkgs_ref:
            if not any(pkg_name in _pkg for _pkg in pkgs):
                raise Exception("pkg_name: %s\n\npip freeze: %s\n\nfreeze.freeze: %s" % (pkg_name, pkgs_ref, pkgs))
            self.assertTrue(any(pkg_name in _pkg for _pkg in pkgs))
