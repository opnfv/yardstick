# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
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

__author__ = 'gpetralx'


import unittest
import experimental_framework.heat_template_generation as heat_gen


class TestTreeNode(unittest.TestCase):
    def setUp(self):
        self.tree = heat_gen.TreeNode()

    def tearDown(self):
        pass

    def test_add_child_for_success(self):
        child = heat_gen.TreeNode()
        self.tree.add_child(child)
        self.assertIn(child, self.tree.down)

    def test_get_parent_for_success(self):
        self.assertIsNone(self.tree.get_parent())
        child = heat_gen.TreeNode()
        self.tree.add_child(child)
        self.assertEqual(self.tree, child.get_parent())

    def test_get_children_for_success(self):
        self.assertListEqual(list(), self.tree.get_children())
        child = heat_gen.TreeNode()
        self.tree.add_child(child)
        children = [child]
        self.assertListEqual(children, self.tree.get_children())

    def test_variable_name_for_success(self):
        self.assertEqual('', self.tree.get_variable_name())
        variable_name = 'test'
        self.tree.set_variable_name(variable_name)
        self.assertEqual(variable_name, self.tree.get_variable_name())

    def test_variable_value_for_success(self):
        self.assertEqual(0, self.tree.get_variable_value())
        variable_value = 1
        self.tree.set_variable_value(variable_value)
        self.assertEqual(variable_value, self.tree.get_variable_value())

    def test_get_path_for_success(self):
        child_1 = heat_gen.TreeNode()
        self.tree.add_child(child_1)
        child_2 = heat_gen.TreeNode()
        child_1.add_child(child_2)
        child_3 = heat_gen.TreeNode()
        child_2.add_child(child_3)

        path = [self.tree, child_1, child_2, child_3]

        self.assertListEqual(path, child_3.get_path())

    def test_str_for_success(self):
        name = 'name'
        value = 0
        self.tree.set_variable_name(name)
        self.tree.set_variable_value(value)
        self.assertEqual(name + " --> " + str(value), str(self.tree))

    def test_repr_for_success(self):
        name = 'name'
        value = 0
        self.tree.set_variable_name(name)
        self.tree.set_variable_value(value)
        self.assertEqual(name + " = " + str(value), repr(self.tree))

    def test_get_leaves_for_success(self):
        child_1 = heat_gen.TreeNode()
        self.tree.add_child(child_1)
        child_2 = heat_gen.TreeNode()
        child_1.add_child(child_2)
        child_3 = heat_gen.TreeNode()
        child_2.add_child(child_3)
        child_4 = heat_gen.TreeNode()
        child_2.add_child(child_4)
        child_5 = heat_gen.TreeNode()
        child_2.add_child(child_5)
        leaves = [child_3, child_4, child_5]
        self.assertListEqual(leaves, heat_gen.TreeNode.get_leaves(self.tree))