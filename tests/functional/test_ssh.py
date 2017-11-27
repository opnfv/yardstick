# Copyright 2017 Intel Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import getpass
import os
import shutil
import tempfile
import unittest

from yardstick import ssh


class SSHTestCase(unittest.TestCase):
    """Test SSH methods against localhost connection"""

    def setUp(self):
        user = getpass.getuser()
        host = 'localhost'
        ssh_path = os.path.expanduser('~') + '/.ssh/'
        key_filenames = [ssh_path + 'id_rsa', ssh_path + 'id_dsa']
        self.test_client = ssh.SSH(user, host, key_filename=key_filenames)
        self.addCleanup(self._close)

    def _close(self):
        self.test_client.close()

    def _delete_tmp_file(self, file_name):
        os.remove(file_name)

    def _delete_tmp_dir(self, dir_name):
        shutil.rmtree(dir_name)

    def test_file_exists(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.flush()
        self.addCleanup(self._delete_tmp_file, tmp_file.name)
        self.assertTrue(self.test_client.file_exists(tmp_file.name))

    def test_file_exists_false(self):
        self.assertFalse(self.test_client.file_exists('non_existing_file'))

    def test_directory_exists(self):
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(self._delete_tmp_dir, tmp_dir)
        self.assertTrue(self.test_client.directory_exists(tmp_dir))

    def test_directory_exists_false(self):
        self.assertFalse(self.test_client.directory_exists('non_existing_dir'))

    def test_create_directory(self):
        os_tmp_dir = tempfile.gettempdir()
        tmp_dir = os.path.join(os_tmp_dir, 'dir1', 'dir2', 'dir3')
        self.addCleanup(self._delete_tmp_dir,
                        os.path.join(os_tmp_dir, 'dir1'))
        self.assertEqual(tmp_dir, self.test_client.create_directory(tmp_dir))
