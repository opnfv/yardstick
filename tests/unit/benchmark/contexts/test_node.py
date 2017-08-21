#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015-2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.node

from __future__ import absolute_import
import os
import unittest
import errno
import mock

from yardstick.common import constants as consts
from yardstick.benchmark.contexts import node


class NodeContextTestCase(unittest.TestCase):

    PREFIX = 'yardstick.benchmark.contexts.node'

    NODES_SAMPLE = "nodes_sample.yaml"
    NODES_DUPLICATE_SAMPLE = "nodes_duplicate_sample.yaml"

    def setUp(self):
        self.test_context = node.NodeContext()
        self.os_path_join = os.path.join

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = self.os_path_join(curr_path, filename)
        return file_path

    def test___init__(self):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.controllers, [])
        self.assertEqual(self.test_context.computes, [])
        self.assertEqual(self.test_context.baremetals, [])
        self.assertEqual(self.test_context.env, {})
        self.assertEqual(self.test_context.attrs, {})

    @mock.patch('{}.os.path.join'.format(PREFIX))
    def test_init_negative(self, mock_path_join):
        special_path = '/foo/bar/error_file'
        error_path = self._get_file_abspath("error_file")

        def path_join(*args):
            if args == (consts.YARDSTICK_ROOT_PATH, error_path):
                return special_path
            return self.os_path_join(*args)

        # we can't count mock_path_join calls because
        # it can catch join calls for .pyc files.
        mock_path_join.side_effect = path_join
        self.test_context.read_config_file = read_mock = mock.Mock()
        read_calls = 0

        with self.assertRaises(KeyError):
            self.test_context.init({})

        self.assertEqual(read_mock.call_count, read_calls)

        attrs = {
            'name': 'foo',
            'file': error_path,
        }
        read_mock.side_effect = IOError(errno.EBUSY, 'busy')
        with self.assertRaises(IOError) as raised:
            self.test_context.init(attrs)

        read_calls += 1
        self.assertEqual(read_mock.called, read_calls)
        self.assertIn(attrs['file'], self.test_context.file_path)
        self.assertEqual(raised.exception.errno, errno.EBUSY)
        self.assertEqual(str(raised.exception), str(read_mock.side_effect))

        read_mock.side_effect = IOError(errno.ENOENT, 'not found')
        with self.assertRaises(IOError) as raised:
            self.test_context.init(attrs)

        read_calls += 2
        self.assertEqual(read_mock.call_count, read_calls)
        self.assertEqual(self.test_context.file_path, special_path)
        self.assertEqual(raised.exception.errno, errno.ENOENT)
        self.assertEqual(str(raised.exception), str(read_mock.side_effect))

    def test_read_config_file(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        self.assertIsNotNone(self.test_context.read_config_file())

    def test__dispatch_script(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        self.test_context.env = {'bash': [{'script': 'dummy'}]}
        self.test_context._execute_script = mock.Mock()
        self.assertEqual(self.test_context._dispatch_script('bash'), None)

    def test__dispatch_ansible(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        self.test_context.env = {'ansible': [{'script': 'dummy'}]}
        self.test_context._do_ansible_job = mock.Mock()
        self.assertEqual(self.test_context._dispatch_ansible('ansible'), None)
        self.test_context.env = {}
        self.assertEqual(self.test_context._dispatch_ansible('ansible'), None)

    @mock.patch("{}.AnsibleCommon".format(PREFIX))
    def test__do_ansible_job(self, mock_ansible):
        self.assertEqual(None, self.test_context._do_ansible_job('dummy'))

    def test_successful_init(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        self.assertEqual(self.test_context.name, "foo")
        self.assertEqual(len(self.test_context.nodes), 4)
        self.assertEqual(len(self.test_context.controllers), 2)
        self.assertEqual(len(self.test_context.computes), 1)
        self.assertEqual(self.test_context.computes[0]["name"], "node3")
        self.assertEqual(len(self.test_context.baremetals), 1)
        self.assertEqual(self.test_context.baremetals[0]["name"], "node4")

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

    def test__get_server_mismatch(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = 'bar.foo1'
        result = self.test_context._get_server(attr_name)

        self.assertEqual(result, None)

    def test__get_server_duplicate(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_DUPLICATE_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = 'node1.foo'
        with self.assertRaises(ValueError):
            self.test_context._get_server(attr_name)

    def test__get_server_found(self):

        attrs = {
            'name': 'foo',
            'file': self._get_file_abspath(self.NODES_SAMPLE)
        }

        self.test_context.init(attrs)

        attr_name = 'node1.foo'
        result = self.test_context._get_server(attr_name)

        self.assertEqual(result['ip'], '10.229.47.137')
        self.assertEqual(result['name'], 'node1.foo')
        self.assertEqual(result['user'], 'root')
        self.assertEqual(result['key_filename'], '/root/.yardstick_key')

    @mock.patch('{}.NodeContext._dispatch_script'.format(PREFIX))
    def test_deploy(self, dispatch_script_mock):
        obj = node.NodeContext()
        obj.env = {
            'type': 'script'
        }
        obj.deploy()
        self.assertTrue(dispatch_script_mock.called)

    @mock.patch('{}.NodeContext._dispatch_ansible'.format(PREFIX))
    def test_deploy_anisible(self, dispatch_ansible_mock):
        obj = node.NodeContext()
        obj.env = {
            'type': 'ansible'
        }
        obj.deploy()
        self.assertTrue(dispatch_ansible_mock.called)

    @mock.patch('{}.NodeContext._dispatch_script'.format(PREFIX))
    def test_undeploy(self, dispatch_script_mock):
        obj = node.NodeContext()
        obj.env = {
            'type': 'script'
        }
        obj.undeploy()
        self.assertTrue(dispatch_script_mock.called)

    @mock.patch('{}.NodeContext._dispatch_ansible'.format(PREFIX))
    def test_undeploy_anisble(self, dispatch_ansible_mock):
        obj = node.NodeContext()
        obj.env = {
            'type': 'ansible'
        }
        obj.undeploy()
        self.assertTrue(dispatch_ansible_mock.called)

    @mock.patch('{}.ssh.SSH._put_file_shell'.format(PREFIX))
    @mock.patch('{}.ssh.SSH.execute'.format(PREFIX))
    def test_execute_remote_script(self, execute_mock, put_file_mock):
        obj = node.NodeContext()
        obj.env = {'prefix': 'yardstick.benchmark.scenarios.compute'}
        node_name_args = 'node5'
        obj.nodes = [{
            'name': node_name_args,
            'user': 'ubuntu',
            'ip': '10.10.10.10',
            'pwd': 'ubuntu',
        }]

        info = {'script': 'computecapacity.bash'}
        execute_mock.return_value = (0, '', '')
        obj._execute_remote_script('node5', info)

        self.assertTrue(put_file_mock.called)
        self.assertTrue(execute_mock.called)

    @mock.patch('{}.NodeContext._execute_local_script'.format(PREFIX))
    def test_execute_script_local(self, local_execute_mock):
        node_name = 'local'
        info = {}
        node.NodeContext()._execute_script(node_name, info)
        self.assertTrue(local_execute_mock.called)

    @mock.patch('{}.NodeContext._execute_remote_script'.format(PREFIX))
    def test_execute_script_remote(self, remote_execute_mock):
        node_name = 'node5'
        info = {}
        node.NodeContext()._execute_script(node_name, info)
        self.assertTrue(remote_execute_mock.called)

    def test_get_script(self):
        script_args = 'hello.bash'
        info_args = {
            'script': script_args
        }
        script, options = node.NodeContext()._get_script(info_args)
        self.assertEqual(script_args, script)
        self.assertEqual('', options)

    def test_node_info(self):
        node_name_args = 'node5'
        obj = node.NodeContext()
        obj.nodes = [{'name': node_name_args, 'check': node_name_args}]
        node_info = obj._get_node_info(node_name_args)
        self.assertEqual(node_info.get('check'), node_name_args)

    @mock.patch('{}.ssh.SSH.wait'.format(PREFIX))
    def test_get_client(self, wait_mock):
        node_name_args = 'node5'
        obj = node.NodeContext()
        obj.nodes = [{
            'name': node_name_args,
            'user': 'ubuntu',
            'ip': '10.10.10.10',
            'pwd': 'ubuntu',
        }]
        obj._get_client(node_name_args)
        self.assertTrue(wait_mock.called)

    def test_get_server(self):
        self.test_context.name = 'vnf1'
        self.test_context.nodes = [{'name': 'my', 'value': 100}]

        with self.assertRaises(ValueError):
            self.test_context.get_server('my.vnf2')

        expected = {'name': 'my.vnf1', 'value': 100, 'interfaces': {}}
        result = self.test_context.get_server('my.vnf1')
        self.assertDictEqual(result, expected)

    def test_get_context_from_server(self):
        self.test_context.name = 'vnf1'
        self.test_context.nodes = [{'name': 'my', 'value': 100}]
        self.test_context.attrs = {'attr1': 200}

        with self.assertRaises(ValueError):
            self.test_context.get_context_from_server('my.vnf2')

        result = self.test_context.get_context_from_server('my.vnf1')
        self.assertIs(result, self.test_context)

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


def main():
    unittest.main()


if __name__ == '__main__':
    main()
