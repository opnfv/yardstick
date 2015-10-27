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


'''
This file contains the code to Generate the heat templates from the base
template
'''

import json
import os
import shutil
from experimental_framework import common
from experimental_framework.constants import framework_parameters as fp


class TreeNode:
    """
    This class represent the node of the configuration tree.\
    Each node represents a single configuration value for a single
    configuration parameter.
    """

    def __init__(self):
        self.up = None
        self.down = []
        self.variable_name = ''
        self.variable_value = 0

    def add_child(self, node):
        """
        Adds a node as a child for the current node
        :param node: node to be added as a child (type: TreeNode)
        :return: None
        """
        node.up = self
        self.down.append(node)

    def get_parent(self):
        """
        Returns the parent node of the current one
        :return type: TreeNode
        """
        return self.up

    def get_children(self):
        """
        Returns the children of the current node
        :return type: list of TreeNode
        """
        if len(self.down) == 0:
            # return [self]
            return []
        return self.down

    def get_variable_name(self):
        """
        Returns the name of the variable correspondent to the current node
        :return type: str
        """
        return self.variable_name

    def get_variable_value(self):
        """
        Returns the value of the variable correspondent to the current node
        :return type: str or int
        """
        return self.variable_value

    def set_variable_name(self, name):
        """
        Sets the name of the variable for the current node
        :param name: Name of the variable (type: str)
        :return None
        """
        self.variable_name = name

    def set_variable_value(self, value):
        """
        Sets the value of the variable for the current node
        :param value: value of the variable (type: str)
        :return None
        """
        self.variable_value = value

    def get_path(self):
        """
        Returns all the path from the current node to the root of the tree.
        :return type: list of TreeNode
        """
        ret_val = []
        if not self.up:
            ret_val.append(self)
            return ret_val
        for node in self.up.get_path():
            ret_val.append(node)
        ret_val.append(self)
        return ret_val

    def __str__(self):
        return str(self.variable_name) + " --> " + str(self.variable_value)

    def __repr__(self):
        return str(self.variable_name) + " = " + str(self.variable_value)

    @staticmethod
    def _get_leaves(node, leaves):
        """
        Returns all the leaves of a tree.
        It changes the "leaves" list.
        :param node: root of the tree (type: TreeNode)
        :param leaves: partial list of leaves (type: list of TreeNode)
        :return type: None
        """
        children = node.get_children()
        if len(children) == 0:
            leaves.append(node)
            return
        for child in children:
            TreeNode._get_leaves(child, leaves)

    @staticmethod
    def get_leaves(node):
        """
        Returns all the leaves of a tree.
        :param node: root of the tree (TreeNode)
        :return type: list
        """
        leaves = list()
        TreeNode._get_leaves(node, leaves)
        return leaves


template_name = fp.EXPERIMENT_TEMPLATE_NAME


def generates_templates(base_heat_template, deployment_configuration):
    """
    Generates the heat templates for the experiments
    :return: None
    """
    # Load useful parameters from file
    template_dir = common.get_template_dir()
    template_file_extension = fp.TEMPLATE_FILE_EXTENSION
    template_base_name = base_heat_template

    variables = deployment_configuration

    # Delete the templates eventually generated in previous running of the
    # framework
    common.LOG.info("Removing the heat templates previously generated")
    os.system("rm " + template_dir + template_name + "_*")

    # Creation of the tree with all the new configurations
    common.LOG.info("Creation of the tree with all the new configurations")
    tree = TreeNode()
    for variable in variables:
        leaves = TreeNode.get_leaves(tree)
        common.LOG.debug("LEAVES: " + str(leaves))
        common.LOG.debug("VALUES: " + str(variables[variable]))

        for value in variables[variable]:
            for leaf in leaves:
                new_node = TreeNode()
                new_node.set_variable_name(variable)
                new_node.set_variable_value(value)
                leaf.add_child(new_node)

    common.LOG.debug("CONFIGURATION TREE: " + str(tree))

    common.LOG.info("Heat Template and metadata file creation")
    leaves = TreeNode.get_leaves(tree)
    counter = 1
    for leaf in leaves:
        heat_template_vars = leaf.get_path()
        if os.path.isabs(template_base_name):
            base_template = template_base_name
        else:
            base_template = template_dir + template_base_name
        if os.path.isabs(template_name):
            new_template = template_name
        else:
            new_template = template_dir + template_name
        new_template += "_" + str(counter) + template_file_extension
        shutil.copy(base_template, new_template)

        metadata = dict()
        for var in heat_template_vars:
            if var.get_variable_name():
                common.replace_in_file(new_template, "#" +
                                       var.get_variable_name(),
                                       var.get_variable_value())
                metadata[var.get_variable_name()] = var.get_variable_value()

        # Save the metadata on a JSON file
        with open(new_template + ".json", 'w') as outfile:
            json.dump(metadata, outfile)

        common.LOG.debug("Heat Templates and Metadata file " + str(counter) +
                         " created")
        counter += 1

    # Creation of the template files
    common.LOG.info(str(counter - 1) + " Heat Templates and Metadata files "
                                       "created")


def get_all_heat_templates(template_dir, template_file_extension):
    """
    Loads and returns all the generated heat templates
    :param template_dir: directory to search in (type: str)
    :param template_file_extension: extension of the file for templates
            (type: str)
    :return: type: list
    """
    template_files = list()
    for dirname, dirnames, filenames in os.walk(template_dir):
        for filename in filenames:
            if template_file_extension in filename and \
                    filename.endswith(template_file_extension) and \
                    template_name in filename:
                template_files.append(filename)
    template_files.sort()
    return template_files
