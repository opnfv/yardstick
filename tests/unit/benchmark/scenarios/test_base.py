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

import unittest
import mock

from yardstick.benchmark.scenarios.base import Scenario, ClientServerScenario, OpenstackScenario


class ScenarioTestCase(unittest.TestCase):

    SCENARIO_TYPE = Scenario

    @classmethod
    def make_runnable_scenario(cls, scenario=None, context=None):
        if cls.SCENARIO_TYPE.LOGGER is None:
            cls.SCENARIO_TYPE.LOGGER = mock.Mock()

        if scenario is None:
            scenario = {}
        if context is None:
            context = {}

        obj = cls.SCENARIO_TYPE(scenario, context)
        obj._run = mock.Mock(return_value=[])
        return obj


class TestScenarioBase(ScenarioTestCase):

    def test_context(self):
        with self.make_runnable_scenario() as obj:
            obj.run('arg')

    def test_property_options_cannot_set_twice(self):
        obj = self.make_runnable_scenario()
        obj.options = {'hello': 'world'}

        with self.assertRaises(RuntimeError):
            obj.options = {}

    def test_property_options_cannot_set_non_mapping(self):
        obj = self.make_runnable_scenario()

        with self.assertRaises(RuntimeError):
            obj.options = 'non_mapping'

    def test_setup_once(self):
        obj = Scenario({}, {})
        obj._setup = mock__setup = mock.Mock(side_effect=[None, AssertionError])

        self.assertEqual(mock__setup.call_count, 0)
        obj.setup()  # _setup called and returns None
        self.assertEqual(mock__setup.call_count, 1)
        obj.setup()  # will raise AssertionError if _setup is called
        self.assertEqual(mock__setup.call_count, 1)

    def test_setup_run_by_run(self):
        obj = self.make_runnable_scenario()
        self.assertFalse(obj.setup_done)
        obj.run('arg')
        self.assertTrue(obj.setup_done)

    def test__run(self):
        with Scenario({}, {}) as obj, self.assertRaises(RuntimeError):
            obj._run('arg')


class TestClientServerScenario(ScenarioTestCase):

    SCENARIO_TYPE = ClientServerScenario

    @mock.patch('yardstick.benchmark.scenarios.base.pkg_resources')
    def test__put_pkg_resource_file(self, *_):
        mock_connection = mock.Mock()

        obj = self.make_runnable_scenario()
        obj._put_pkg_resource_file(mock_connection, 'my_file_name', 'target_name', 'module/path')
        self.assertEqual(mock_connection.put_file_shell.call_count, 1)

    @mock.patch('yardstick.benchmark.scenarios.base.pkg_resources')
    def test__run_pkg_resource_file(self, *_):
        mock_connection = mock.Mock()

        obj = self.make_runnable_scenario()
        obj._run_pkg_resource_file(mock_connection, 'my_file_name', 'target_name', 'module/path')
        self.assertEqual(mock_connection.put_file_shell.call_count, 1)
        self.assertEqual(mock_connection.execute.call_count, 1)

    @mock.patch('yardstick.benchmark.scenarios.base.pkg_resources')
    def test__put_pkg_resource_files(self, *_):
        mock_connection = mock.Mock()

        obj = self.make_runnable_scenario()
        obj.RESOURCE_FILE_MAP.update({
            'local1': 'remote1',
            'local2': 'remote2',
            'local3': 'remote3',
        })
        obj._put_pkg_resource_files(mock_connection)
        self.assertEqual(mock_connection.put_file_shell.call_count, 3)

    @mock.patch('yardstick.benchmark.scenarios.base.pkg_resources')
    def test__run_pkg_resource_files(self, *_):
        mock_connection = mock.Mock()

        obj = self.make_runnable_scenario()
        obj.RESOURCE_FILE_MAP.update({
            'local1': 'remote1',
            'local2': 'remote2',
            'local3': 'remote3',
        })
        obj._run_pkg_resource_files(mock_connection)
        self.assertEqual(mock_connection.put_file_shell.call_count, 3)
        self.assertEqual(mock_connection.execute.call_count, 3)

    def test_duration_attribute(self):
        obj = self.make_runnable_scenario({'runner': {'duration': 123}})
        self.assertEqual(obj.duration, 123)

        obj = self.make_runnable_scenario({'options': {'duration': 321}})
        self.assertEqual(obj.duration, 321)

        obj = self.make_runnable_scenario()
        self.assertEqual(obj.duration, obj.DEFAULT_DURATION)

    @mock.patch('yardstick.benchmark.scenarios.base.open')
    @mock.patch('yardstick.benchmark.scenarios.base.TaskTemplate')
    @mock.patch('yardstick.benchmark.scenarios.base.yaml_load')
    def test_nodes_attribute(self, mock_yaml_load, *_):
        mock_yaml_load.return_value = {
            'nodes': [
                {
                    'host_name': 'node1',
                    'key1': 'value1',
                },
            ],
        }

        obj = self.make_runnable_scenario({'options': {'file': 'my_file'}})
        self.assertIsNone(obj._nodes)
        self.assertIn('node1', obj.nodes)
        self.assertIsNotNone(obj._nodes)

    def test_server_data(self):
        target_node = {'key1': 'value1'}
        obj = self.make_runnable_scenario(context={'target': target_node})
        self.assertDictEqual(obj.server_data, target_node)

    def test_server_ssh(self):
        target_node = {'key1': 'value1'}
        obj = self.make_runnable_scenario(context={'target': target_node})
        obj.make_ssh_client = mock_make_ssh_client = mock.Mock()
        mock_ssh_client = mock_make_ssh_client()

        self.assertIsNone(obj._server_ssh)
        self.assertEqual(obj.server_ssh, mock_ssh_client)
        self.assertEqual(obj._server_ssh, mock_ssh_client)

    def test_client_data(self):
        target_node = {'key1': 'value1'}
        obj = self.make_runnable_scenario(context={'host': target_node})
        self.assertDictEqual(obj.client_data, target_node)

    def test_client_ssh(self):
        target_node = {'key1': 'value1'}
        obj = self.make_runnable_scenario(context={'host': target_node})
        obj.make_ssh_client = mock_make_ssh_client = mock.Mock()
        mock_ssh_client = mock_make_ssh_client()

        self.assertIsNone(obj._client_ssh)
        self.assertEqual(obj.client_ssh, mock_ssh_client)
        self.assertEqual(obj._client_ssh, mock_ssh_client)

    def test__exec_cmd_to_client_and_server(self):
        host_node = {'key1': 'value1'}
        target_node = {'key2': 'value2'}
        obj = self.make_runnable_scenario(context={'host': host_node, 'target': target_node})
        obj._nodes = {}
        obj.make_ssh_client = mock_make_ssh_client = mock.Mock()
        mock_ssh_client = mock_make_ssh_client()
        mock_ssh_client.execute_with_raise.return_value = ''

        obj._exec_cmd_to_client_and_server('cmd')
        self.assertEqual(mock_make_ssh_client.call_count, 3)  # one here and two during the call
        self.assertEqual(mock_ssh_client.execute_with_raise.call_count, 2)


class TestOpenstackScenario(ScenarioTestCase):

    SCENARIO_TYPE = OpenstackScenario

    @mock.patch('yardstick.benchmark.scenarios.base.utils')
    def test_host_name(self, mock_utils):
        mock_utils.change_obj_to_dict.return_value = {'OS-EXT-SRV-ATTR:host': ' hostname1\t'}
        obj = self.make_runnable_scenario()
        obj._current_server = mock.Mock()

        self.assertIsNone(obj._host_name)
        self.assertEqual(obj.host_name, 'hostname1')
        self.assertIsNotNone(obj._host_name)
