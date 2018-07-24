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

import collections
import shutil
import subprocess
import tempfile

import mock
from six import moves
from six.moves import configparser

from yardstick.common import ansible_common
from yardstick.tests.unit import base as ut_base


class OverwriteDictTestCase(ut_base.BaseUnitTestCase):

    def test_overwrite_dict_cfg(self):
        c = configparser.ConfigParser(allow_no_value=True)
        d = {
            "section_a": "empty_value",
            "section_b": {"key_c": "Val_d", "key_d": "VAL_D"},
            "section_c": ["key_c", "key_d"],
        }
        ansible_common.overwrite_dict_to_cfg(c, d)
        # Python3 and Python2 convert empty values into None or ''
        # we don't really care but we need to compare correctly for unittest
        self.assertTrue(c.has_option("section_a", "empty_value"))
        self.assertEqual(sorted(c.items("section_b")),
                         [('key_c', 'Val_d'), ('key_d', 'VAL_D')])
        self.assertTrue(c.has_option("section_c", "key_c"))
        self.assertTrue(c.has_option("section_c", "key_d"))


class FilenameGeneratorTestCase(ut_base.BaseUnitTestCase):

    @mock.patch.object(tempfile, 'NamedTemporaryFile')
    def test__handle_existing_file(self, _):
        ansible_common.FileNameGenerator._handle_existing_file('/dev/null')

    def test_get_generator_from_file(self):
        ansible_common.FileNameGenerator.get_generator_from_filename(
            '/dev/null', '', '', '')

    def test_get_generator_from_file_middle(self):
        ansible_common.FileNameGenerator.get_generator_from_filename(
            '/dev/null', '', '', 'null')

    def test_get_generator_from_file_prefix(self):
        ansible_common.FileNameGenerator.get_generator_from_filename(
            '/dev/null', '', 'null', 'middle')


class AnsibleNodeTestCase(ut_base.BaseUnitTestCase):

    def test_ansible_node_len(self):
        self.assertEqual(0, len(ansible_common.AnsibleNode()))

    def test_ansible_node_repr(self):
        self.assertEqual('AnsibleNode<{}>', repr(ansible_common.AnsibleNode()))

    def test_ansible_node_iter(self):
        node = ansible_common.AnsibleNode(data={'a': 1, 'b': 2, 'c': 3})
        for key in node:
            self.assertIn(key, ('a', 'b', 'c'))

    def test_is_role(self):
        node = ansible_common.AnsibleNode()
        self.assertFalse(node.is_role('', default='foo'))

    def test_ansible_node_get_tuple(self):
        node = ansible_common.AnsibleNode({'name': 'name'})
        self.assertEqual(node.get_tuple(), ('name', node))

    def test_gen_inventory_line(self):
        a = ansible_common.AnsibleNode(collections.defaultdict(str))
        self.assertEqual(a.gen_inventory_line(), "")

    def test_ansible_node_delitem(self):
        node = ansible_common.AnsibleNode({'name': 'name'})
        self.assertEqual(1, len(node))
        del node['name']
        self.assertEqual(0, len(node))

    def test_ansible_node_getattr(self):
        node = ansible_common.AnsibleNode({'name': 'name'})
        self.assertIsNone(getattr(node, 'nosuch', None))


class AnsibleNodeDictTestCase(ut_base.BaseUnitTestCase):

    def test_ansible_node_dict_len(self):
        n = ansible_common.AnsibleNode
        a = ansible_common.AnsibleNodeDict(n, {})
        self.assertEqual(0, len(a))

    def test_ansible_node_dict_repr(self):
        n = ansible_common.AnsibleNode
        a = ansible_common.AnsibleNodeDict(n, {})
        self.assertEqual('{}', repr(a))

    def test_ansible_node_dict_get(self):
        n = ansible_common.AnsibleNode
        a = ansible_common.AnsibleNodeDict(n, {})
        self.assertIsNone(a.get(""))

    def test_gen_inventory_lines_for_all_of_type(self):
        n = ansible_common.AnsibleNode
        a = ansible_common.AnsibleNodeDict(n, {})
        self.assertEqual(a.gen_inventory_lines_for_all_of_type(""), [])

    def test_gen_inventory_lines(self):
        n = ansible_common.AnsibleNode
        a = ansible_common.AnsibleNodeDict(n, [{
            "name": "name", "user": "user", "password": "PASS",
            "role": "role",
        }])
        self.assertEqual(a.gen_all_inventory_lines(),
                         ["name ansible_ssh_pass=PASS ansible_user=user"])


class AnsibleCommonTestCase(ut_base.BaseUnitTestCase):

    @staticmethod
    def _delete_tmpdir(dir):
        shutil.rmtree(dir)

    def test_get_timeouts(self):
        self.assertAlmostEqual(
            ansible_common.AnsibleCommon.get_timeout(-100), 1200.0)

    def test_reset(self):
        a = ansible_common.AnsibleCommon({})
        a.reset()

    def test_do_install_no_dir(self):
        a = ansible_common.AnsibleCommon({})
        self.assertRaises(OSError, a.do_install, '', '')

    def test_gen_inventory_dict(self):
        nodes = [{
            "name": "name", "user": "user", "password": "PASS",
            "role": "role",
        }]
        a = ansible_common.AnsibleCommon(nodes)
        a.gen_inventory_ini_dict()
        self.assertEqual(a.inventory_dict, {
            'nodes': ['name ansible_ssh_pass=PASS ansible_user=user'],
            'role': ['name']
        })

    def test_deploy_dir(self):
        a = ansible_common.AnsibleCommon({})
        self.assertRaises(ValueError, getattr, a, "deploy_dir")

    def test_deploy_dir_set(self):
        a = ansible_common.AnsibleCommon({})
        a.deploy_dir = ""

    def test_deploy_dir_set_get(self):
        a = ansible_common.AnsibleCommon({})
        a.deploy_dir = "d"
        self.assertEqual(a.deploy_dir, "d")

    @mock.patch.object(moves.builtins, 'open')
    def test__gen_ansible_playbook_file_list(self, *args):
        d = tempfile.mkdtemp()
        self.addCleanup(self._delete_tmpdir, d)
        a = ansible_common.AnsibleCommon({})
        a._gen_ansible_playbook_file(["a"], d)

    @mock.patch.object(tempfile, 'NamedTemporaryFile')
    @mock.patch.object(moves.builtins, 'open')
    def test__gen_ansible_inventory_file(self, *args):
        nodes = [{
            "name": "name", "user": "user", "password": "PASS",
            "role": "role",
        }]
        d = tempfile.mkdtemp()
        self.addCleanup(self._delete_tmpdir, d)
        a = ansible_common.AnsibleCommon(nodes)
        a.gen_inventory_ini_dict()
        inv_context = a._gen_ansible_inventory_file(d)
        with inv_context:
            c = moves.StringIO()
            inv_context.write_func(c)
            self.assertIn("ansible_ssh_pass=PASS", c.getvalue())

    @mock.patch.object(tempfile, 'NamedTemporaryFile')
    @mock.patch.object(moves.builtins, 'open')
    def test__gen_ansible_playbook_file_list_multiple(self, *args):
        d = tempfile.mkdtemp()
        self.addCleanup(self._delete_tmpdir, d)
        a = ansible_common.AnsibleCommon({})
        a._gen_ansible_playbook_file(["a", "b"], d)

    @mock.patch.object(tempfile, 'NamedTemporaryFile')
    @mock.patch.object(subprocess, 'Popen')
    @mock.patch.object(moves.builtins, 'open')
    def test_do_install_tmp_dir(self, _, mock_popen, *args):
        mock_popen.return_value.communicate.return_value = "", ""
        mock_popen.return_value.wait.return_value = 0
        d = tempfile.mkdtemp()
        self.addCleanup(self._delete_tmpdir, d)
        a = ansible_common.AnsibleCommon({})
        a.do_install('', d)

    @mock.patch.object(tempfile, 'NamedTemporaryFile')
    @mock.patch.object(moves.builtins, 'open')
    @mock.patch.object(subprocess, 'Popen')
    def test_execute_ansible_check(self, mock_popen, *args):
        mock_popen.return_value.communicate.return_value = "", ""
        mock_popen.return_value.wait.return_value = 0
        d = tempfile.mkdtemp()
        self.addCleanup(self._delete_tmpdir, d)
        a = ansible_common.AnsibleCommon({})
        a.execute_ansible('', d, ansible_check=True, verbose=True)

    def test_get_sut_info(self):
        d = tempfile.mkdtemp()
        a = ansible_common.AnsibleCommon({})
        self.addCleanup(self._delete_tmpdir, d)
        with mock.patch.object(a, '_exec_get_sut_info_cmd'):
            a.get_sut_info(d)

    def test_get_sut_info_not_exist(self):
        a = ansible_common.AnsibleCommon({})
        with self.assertRaises(OSError):
            a.get_sut_info('/hello/world')
