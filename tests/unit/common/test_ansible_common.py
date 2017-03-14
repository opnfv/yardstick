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
from collections import defaultdict

import mock
import unittest

from six.moves.configparser import ConfigParser

from yardstick.common import ansible_common

PREFIX = 'yardstick.common.ansible_common'


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


class FilenameGeneratorTestCase(unittest.TestCase):
    @mock.patch('{}.NamedTemporaryFile'.format(PREFIX))
    def test__handle_existing_file(self, mock_tmp):
        f = ansible_common.FileNameGenerator._handle_existing_file("/dev/null")


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

    def test_is_role(self):
        a = ansible_common.AnsibleNode()
        self.assertFalse(a.is_role("", default="foo"))

    def test_gen_inventory_line(self):
        a = ansible_common.AnsibleNode(defaultdict(str))
        self.assertEqual(a.gen_inventory_line(), "")


class AnsibleNodeDictTestCase(unittest.TestCase):
    def test_ansible_node_dict(self):
        n = ansible_common.AnsibleNode()
        a = ansible_common.AnsibleNodeDict(n, {})

    def test_ansible_node_dict_len(self):
        n = ansible_common.AnsibleNode()
        a = ansible_common.AnsibleNodeDict(n, {})
        len(a)

    def test_ansible_node_dict_repr(self):
        n = ansible_common.AnsibleNode()
        a = ansible_common.AnsibleNodeDict(n, {})
        repr(a)

    def test_ansible_node_dict_iter(self):
        n = ansible_common.AnsibleNode()
        a = ansible_common.AnsibleNodeDict(n, {})
        for _ in a:
            pass

    def test_gen_inventory_lines_for_all_of_type(self):
        n = ansible_common.AnsibleNode()
        a = ansible_common.AnsibleNodeDict(n, {})
        self.assertEqual(a.gen_inventory_lines_for_all_of_type(""), [])


class AnsibleCommonTestCase(unittest.TestCase):
    def test_get_timeouts(self):
        self.assertAlmostEquals(ansible_common.AnsibleCommon.get_timeout(-100), 1200.0)

    def test__init__(self):
        a = ansible_common.AnsibleCommon({})

    def test_reset(self):
        a = ansible_common.AnsibleCommon({})
        a.reset()

    def test_do_install_no_dir(self):
        a = ansible_common.AnsibleCommon({})
        self.assertRaises(OSError, a.do_install, '', '')

    def test_deploy_dir(self):
        a = ansible_common.AnsibleCommon({})
        self.assertRaises(ValueError, getattr, a, "deploy_dir")

    @mock.patch('{}.open'.format(PREFIX))
    def test__gen_ansible_playbook_file_list(self, mock_open):
        d = tempfile.mkdtemp()
        try:
            a = ansible_common.AnsibleCommon({})
            a._gen_ansible_playbook_file(["a"], d)
        finally:
            os.rmdir(d)

    @mock.patch('{}.NamedTemporaryFile'.format(PREFIX))
    @mock.patch('{}.open'.format(PREFIX))
    def test__gen_ansible_playbook_file_list_multiple(self, mock_open, mock_tmp):
        d = tempfile.mkdtemp()
        try:
            a = ansible_common.AnsibleCommon({})
            a._gen_ansible_playbook_file(["a", "b"], d)
        finally:
            os.rmdir(d)

    @mock.patch('{}.NamedTemporaryFile'.format(PREFIX))
    @mock.patch('{}.Popen'.format(PREFIX))
    @mock.patch('{}.open'.format(PREFIX))
    def test_do_install_tmp_dir(self, mock_open, mock_popen, mock_tmp):
        mock_popen.return_value.communicate.return_value = "", ""
        mock_popen.return_value.wait.return_value = 0
        d = tempfile.mkdtemp()
        try:
            a = ansible_common.AnsibleCommon({})
            a.do_install('', d)
        finally:
            os.rmdir(d)

    @mock.patch('{}.NamedTemporaryFile'.format(PREFIX))
    @mock.patch('{}.Popen'.format(PREFIX))
    @mock.patch('{}.open'.format(PREFIX))
    def test_execute_ansible_check(self, mock_open, mock_popen, mock_tmp):
        mock_popen.return_value.communicate.return_value = "", ""
        mock_popen.return_value.wait.return_value = 0
        d = tempfile.mkdtemp()
        try:
            a = ansible_common.AnsibleCommon({})
            a.execute_ansible('', d, ansible_check=True)
        finally:
            os.rmdir(d)
