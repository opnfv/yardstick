#!/usr/bin/env python

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

# Unittest for yardstick.benchmark.contexts.standalone

from __future__ import absolute_import
import os
import unittest

from yardstick.benchmark.contexts import standalone


class StandaloneContextTestCase(unittest.TestCase):

    NODES_SAMPLE = "standalone_sample.yaml"
    NODES_DUPLICATE_SAMPLE = "standalone_duplicate_sample.yaml"

    def setUp(self):
        self.test_context = standalone.StandaloneContext()

    def test_construct(self):

        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.nfvi_node, [])

    def test_unsuccessful_init(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath("error_file")
        }

        self.assertRaises(IOError, self.test_context.init, attrs)

    def test_successful_init(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        self.assertEqual(self.test_context.name, "foo")
        self.assertEqual(len(self.test_context.nodes), 3)
        self.assertEqual(len(self.test_context.nfvi_node), 1)
        self.assertEqual(self.test_context.nfvi_node[0]["name"], "node2")

    def test__get_server_with_dic_attr_name(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = {'name': 'foo.bar'}
        result = self.test_context._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_not_found(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = 'bar.foo'
        result = self.test_context._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_duplicate(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = 'node2.foo'

        self.assertRaises(ValueError, self.test_context._get_server, attr_name)

    def test__get_server_found(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = 'node1.foo'
        result = self.test_context._get_server(attr_name)

        self.assertEqual(result['ip'], '1.1.1.1')
        self.assertEqual(result['name'], 'node1.foo')
        self.assertEqual(result['user'], 'root')

    def test_deploy(self):
        self.assertIsNone(self.test_context.deploy())

    def test_undeploy(self):
        self.assertIsNone(self.test_context.undeploy())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def test__get_network(self):
        network1 = {
            'name': 'net_1',
            'vld_id': 'vld111',
            'segmentation_id': 'seg54',
            'network_type': 'type_a',
            'physical_network': 'phys',
        }
        network2 = {
            'name': 'net_2',
            'vld_id': 'vld999',
        }
        self.test_context.networks = {
            'a': network1,
            'b': network2,
        }

        attr_name = {}
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'vld_id': 'vld777'}
        self.assertIsNone(self.test_context._get_network(attr_name))

        self.assertIsNone(self.test_context._get_network(None))

        attr_name = 'vld777'
        self.assertIsNone(self.test_context._get_network(attr_name))

        attr_name = {'vld_id': 'vld999'}
        expected = {
            "name": 'net_2',
            "vld_id": 'vld999',
            "segmentation_id": None,
            "network_type": None,
            "physical_network": None,
        }
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)

        attr_name = 'a'
        expected = network1
        result = self.test_context._get_network(attr_name)
        self.assertDictEqual(result, expected)
