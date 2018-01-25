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
from yardstick.common import utils
from yardstick.tests.functional import base


class PipPackagesTestCase(base.BaseFunctionalTestCase):

    TMP_FOLDER = '/tmp/pip_packages/'
    PYTHONPATH = 'PYTHONPATH=%s' % TMP_FOLDER

    def setUp(self):
        super(PipPackagesTestCase, self).setUp()
        privsep_helper = os.path.join(
            os.getenv('VIRTUAL_ENV'), 'bin', 'privsep-helper')
        self.config(
            helper_command=' '.join(['sudo', '-EH', privsep_helper]),
            group='yardstick_privileged')
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        utils.execute_command('sudo rm -rf %s' % self.TMP_FOLDER)

    def _remove_package(self, package):
        os.system('%s pip uninstall %s -y' % (self.PYTHONPATH, package))

    def _list_packages(self):
        pip_list_regex = re.compile(
            r"(?P<name>[\w\.-]+) \((?P<version>[\w\d_\.\-]+),*.*\)")
        pkg_dict = {}
        pkgs = utils.execute_command('pip list',
                                     env={'PYTHONPATH': self.TMP_FOLDER})
        for line in pkgs:
            match = pip_list_regex.match(line)
            if match and match.group('name'):
                pkg_dict[match.group('name')] = match.group('version')
        return pkg_dict

    def test_install_from_folder(self):
        dirname = path.dirname(__file__)
        package_dir = dirname + '/fake_directory_package'
        package_name = 'yardstick-new-plugin-2'
        self.addCleanup(self._remove_package, package_name)
        self._remove_package(package_name)
        self.assertFalse(package_name in self._list_packages())

        self.assertEqual(0, packages.pip_install(package_dir, self.TMP_FOLDER))
        self.assertTrue(package_name in self._list_packages())

    def test_install_from_pip_package(self):
        dirname = path.dirname(__file__)
        package_path = (dirname +
                        '/fake_pip_package/yardstick_new_plugin-1.0.0.tar.gz')
        package_name = 'yardstick-new-plugin'
        self.addCleanup(self._remove_package, package_name)
        self._remove_package(package_name)
        self.assertFalse(package_name in self._list_packages())

        self.assertEqual(0, packages.pip_install(package_path, self.TMP_FOLDER))
        self.assertTrue(package_name in self._list_packages())

    # NOTE(ralonsoh): an stable test plugin project is needed in OPNFV git
    # server to execute this test.
    # def test_install_from_url(self):

    def test_pip_freeze(self):
        # NOTE (ralonsoh): from requirements.txt file. The best way to test
        # this function is to parse requirements.txt and test-requirements.txt
        # and check all packages.
        pkgs_ref = {'Babel': '2.3.4',
                    'SQLAlchemy': '1.1.12',
                    'influxdb': '4.1.1',
                    'netifaces': '0.10.6',
                    'unicodecsv': '0.14.1'}
        pkgs = packages.pip_list()
        for name, version in (pkgs_ref.items()):
            self.assertEqual(version, pkgs[name])
