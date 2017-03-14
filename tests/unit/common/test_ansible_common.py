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


from __future__ import absolute_import

import os
import tempfile

import mock
import unittest

from six.moves.configparser import ConfigParser

from yardstick.common import ansible_common


class OverwriteDictTestCase(unittest.TestCase):
    def test_overwrite_dict_cfg(self):
        c = ConfigParser(allow_no_value=True)
        d = {
            "section_a": "empty_value",
            "section_b": {"key_c": "val_d", "key_d": "val_d"},
        }
        ansible_common.overwrite_dict_to_cfg(c, d)
        c_items = {s: sorted(c.items(s)) for s in c.sections()}
        self.assertDictEqual(c_items, {
            'section_a': [('empty_value', '')],
            'section_b': [('key_c', 'val_d'), ('key_d', 'val_d')]
        })


class AnsibleNodeTestCase(unittest.TestCase):
    def test_ansible_node(self):
        a = ansible_common.AnsibleNode()

    def test_ansible_node_len(self):
        a = ansible_common.AnsibleNode()
        len(a)

    def test_ansible_node_repr(self):
        a = ansible_common.AnsibleNode()
        repr(a)

    def test_ansible_node_iter(self):
        a = ansible_common.AnsibleNode()
        for _ in a:
            pass


class AnsibleNodeDictTestCase(unittest.TestCase):
    def test_ansible_node_dict(self):
        n = ansible_common.AnsibleNode()
        a = ansible_common.AnsibleNodeDict(n, {})


class AnsibleCommonTestCase(unittest.TestCase):
    PREFIX = 'yardstick.common.ansible_common'

    def test__init__(self):
        a = ansible_common.AnsibleCommon({})

    def test_reset(self):
        a = ansible_common.AnsibleCommon({})
        a.reset()

    def test_do_install_no_dir(self):
        a = ansible_common.AnsibleCommon({})
        self.assertRaises(OSError, a.do_install, '', '')

    @mock.patch('{}.Popen'.format(PREFIX))
    @mock.patch('{}.open'.format(PREFIX))
    def test_do_install_tmp_dir(self, mock_open, mock_popen):
        mock_popen.return_value.communicate.return_value = "", ""
        mock_popen.return_value.wait.return_value = 0
        d = tempfile.mkdtemp()
        try:
            a = ansible_common.AnsibleCommon({})
            a.do_install('', d)
        finally:
            os.rmdir(d)
