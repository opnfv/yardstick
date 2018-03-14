##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy
import io
import os
import sys

import mock
import six
import unittest
import uuid

from yardstick.benchmark.contexts import dummy
from yardstick.benchmark.core import task
from yardstick.common import constants as consts
from yardstick.common import exceptions
from yardstick.common import task_template
from yardstick.common import utils


class TaskTestCase(unittest.TestCase):

    @mock.patch.object(task, 'Context')
    def test_parse_nodes_with_context_same_context(self, mock_context):
        scenario_cfg = {
            "nodes": {
                "host": "node1.LF",
                "target": "node2.LF"
            }
        }
        server_info = {
            "ip": "10.20.0.3",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        mock_context.get_server.return_value = server_info

        context_cfg = task.parse_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["host"], server_info)
        self.assertEqual(context_cfg["target"], server_info)

    def test_set_dispatchers(self):
        t = task.Task()
        output_config = {"DEFAULT": {"dispatcher": "file, http"}}
        t._set_dispatchers(output_config)
        self.assertEqual(output_config, output_config)

    @mock.patch.object(task, 'DispatcherBase')
    def test__do_output(self, mock_dispatcher):
        t = task.Task()
        output_config = {"DEFAULT": {"dispatcher": "file, http"}}

        dispatcher1 = mock.MagicMock()
        dispatcher1.__dispatcher_type__ = 'file'

        dispatcher2 = mock.MagicMock()
        dispatcher2.__dispatcher_type__ = 'http'

        mock_dispatcher.get = mock.MagicMock(return_value=[dispatcher1,
                                                           dispatcher2])
        self.assertIsNone(t._do_output(output_config, {}))

    @mock.patch.object(task, 'Context')
    def test_parse_networks_from_nodes(self, mock_context):
        nodes = {
            'node1': {
                'interfaces': {
                    'mgmt': {
                        'network_name': 'mgmt',
                    },
                    'xe0': {
                        'network_name': 'uplink_0',
                    },
                    'xe1': {
                        'network_name': 'downlink_0',
                    },
                },
            },
            'node2': {
                'interfaces': {
                    'mgmt': {
                        'network_name': 'mgmt',
                    },
                    'uplink_0': {
                        'network_name': 'uplink_0',
                    },
                    'downlink_0': {
                        'network_name': 'downlink_0',
                    },
                },
            },
        }

        mock_context.get_network.side_effect = iter([
            None,
            {
                'name': 'mgmt',
                'network_type': 'flat',
            },
            {},
            {
                'name': 'uplink_0',
                'subnet_cidr': '10.20.0.0/16',
            },
            {
                'name': 'downlink_0',
                'segmentation_id': '1001',
            },
            {
                'name': 'uplink_1',
            },
        ])

        # one for each interface
        expected_get_network_calls = 6
        expected = {
            'mgmt': {'name': 'mgmt', 'network_type': 'flat'},
            'uplink_0': {'name': 'uplink_0', 'subnet_cidr': '10.20.0.0/16'},
            'uplink_1': {'name': 'uplink_1'},
            'downlink_0': {'name': 'downlink_0', 'segmentation_id': '1001'},
        }

        networks = task.get_networks_from_nodes(nodes)
        self.assertEqual(mock_context.get_network.call_count, expected_get_network_calls)
        self.assertDictEqual(networks, expected)

    @mock.patch.object(task, 'Context')
    @mock.patch.object(task, 'base_runner')
    def test_run(self, mock_base_runner, *args):
        scenario = {
            'host': 'athena.demo',
            'target': 'ares.demo',
            'runner': {
                'duration': 60,
                'interval': 1,
                'type': 'Duration'
            },
            'type': 'Ping'
        }

        t = task.Task()
        runner = mock.Mock()
        runner.join.return_value = 0
        runner.get_output.return_value = {}
        runner.get_result.return_value = []
        mock_base_runner.Runner.get.return_value = runner
        t._run([scenario], False, "yardstick.out")
        runner.run.assert_called_once()

    @mock.patch.object(os, 'environ')
    def test_check_precondition(self, mock_os_environ):
        cfg = {
            'precondition': {
                'installer_type': 'compass',
                'deploy_scenarios': 'os-nosdn',
                'pod_name': 'huawei-pod1'
            }
        }

        t = task.TaskParser('/opt')
        mock_os_environ.get.side_effect = ['compass',
                                           'os-nosdn',
                                           'huawei-pod1']
        result = t._check_precondition(cfg)
        self.assertTrue(result)

    def test_parse_suite_no_constraint_no_args(self):
        SAMPLE_SCENARIO_PATH = "no_constraint_no_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch.object(os, 'environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()

        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertIsNone(task_args[1])
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_suite_no_constraint_with_args(self):
        SAMPLE_SCENARIO_PATH = "no_constraint_with_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch.object(os, 'environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()

        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertEqual(task_args[1],
                         '{"host": "node1.LF","target": "node2.LF"}')
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_suite_with_constraint_no_args(self):
        SAMPLE_SCENARIO_PATH = "with_constraint_no_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch.object(os, 'environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()
        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertIsNone(task_args[1])
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_suite_with_constraint_with_args(self):
        SAMPLE_SCENARIO_PATH = "with_constraint_with_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch('os.environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()

        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertEqual(task_args[1],
                         '{"host": "node1.LF","target": "node2.LF"}')
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_options(self):
        options = {
            'openstack': {
                'EXTERNAL_NETWORK': '$network'
            },
            'nodes': ['node1', '$node'],
            'host': '$host'
        }

        t = task.Task()
        t.outputs = {
            'network': 'ext-net',
            'node': 'node2',
            'host': 'server.yardstick'
        }

        expected_result = {
            'openstack': {
                'EXTERNAL_NETWORK': 'ext-net'
            },
            'nodes': ['node1', 'node2'],
            'host': 'server.yardstick'
        }

        actual_result = t._parse_options(options)
        self.assertEqual(expected_result, actual_result)

    def test_parse_options_no_teardown(self):
        options = {
            'openstack': {
                'EXTERNAL_NETWORK': '$network'
            },
            'nodes': ['node1', '$node'],
            'host': '$host',
            'contexts' : {'name': "my-context",
                          'no_teardown': True}
        }

        t = task.Task()
        t.outputs = {
            'network': 'ext-net',
            'node': 'node2',
            'host': 'server.yardstick'
        }

        expected_result = {
            'openstack': {
                'EXTERNAL_NETWORK': 'ext-net'
            },
            'nodes': ['node1', 'node2'],
            'host': 'server.yardstick',
            'contexts': {'name': 'my-context',
                         'no_teardown': True,
                        }
        }

        actual_result = t._parse_options(options)
        self.assertEqual(expected_result, actual_result)

    @mock.patch('six.moves.builtins.open', side_effect=mock.mock_open())
    @mock.patch.object(task, 'utils')
    @mock.patch('logging.root')
    def test_set_log(self, mock_logging_root, *args):
        task_obj = task.Task()
        task_obj.task_id = 'task_id'
        task_obj._set_log()
        mock_logging_root.addHandler.assert_called()

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def change_to_abspath(self, filepath):
        return os.path.join(consts.YARDSTICK_ROOT_PATH, filepath)


class TaskParserTestCase(unittest.TestCase):

    TASK = """
{% set value1 = value1 or 'var1' %}
{% set value2 = value2 or 'var2' %}
key1: {{ value1 }}
key2:
    - {{ value2 }}"""

    TASK_RENDERED_1 = u"""


key1: var1
key2:
    - var2"""

    TASK_RENDERED_2 = u"""


key1: var3
key2:
    - var4"""

    def setUp(self):
        self.parser = task.TaskParser('fake/path')
        self.scenario = {
            'host': 'athena.demo',
            'target': 'kratos.demo',
            'targets': [
                'ares.demo', 'mars.demo'
                ],
            'options': {
                'server_name': {
                    'host': 'jupiter.demo',
                    'target': 'saturn.demo',
                    },
                },
            'nodes': {
                'tg__0': 'tg_0.demo',
                'vnf__0': 'vnf_0.demo',
                }
            }

    def test__change_node_names(self):

        ctx_attrs = {
            'name': 'demo',
            'task_id': '1234567890',
            'servers': [
                'athena', 'kratos',
                'ares', 'mars',
                'jupiter', 'saturn',
                'tg_0', 'vnf_0'
                ]
            }

        my_context = dummy.DummyContext()
        my_context.init(ctx_attrs)

        expected_scenario = {
            'host': 'athena.demo-12345678',
            'target': 'kratos.demo-12345678',
            'targets': [
                'ares.demo-12345678', 'mars.demo-12345678'
                ],
            'options': {
                'server_name': {
                    'host': 'jupiter.demo-12345678',
                    'target': 'saturn.demo-12345678',
                    },
                },
            'nodes': {
                'tg__0': 'tg_0.demo-12345678',
                'vnf__0': 'vnf_0.demo-12345678',
                }
            }

        scenario = copy.deepcopy(self.scenario)

        self.parser._change_node_names(scenario, [my_context])
        self.assertEqual(scenario, expected_scenario)

    def test__change_node_names_context_not_found(self):
        scenario = copy.deepcopy(self.scenario)
        self.assertRaises(exceptions.ScenarioConfigContextNameNotFound,
                          self.parser._change_node_names,
                          scenario, [])

    def test__change_node_names_context_name_unchanged(self):
        ctx_attrs = {
            'name': 'demo',
            'task_id': '1234567890',
            'flags': {
                'no_setup': True,
                'no_teardown': True
                }
            }

        my_context = dummy.DummyContext()
        my_context.init(ctx_attrs)

        scenario = copy.deepcopy(self.scenario)
        expected_scenario = copy.deepcopy(self.scenario)

        self.parser._change_node_names(scenario, [my_context])
        self.assertEqual(scenario, expected_scenario)

    def test__change_node_names_options_empty(self):
        ctx_attrs = {
            'name': 'demo',
            'task_id': '1234567890'
        }

        my_context = dummy.DummyContext()
        my_context.init(ctx_attrs)
        scenario = copy.deepcopy(self.scenario)
        scenario['options'] = None

        self.parser._change_node_names(scenario, [my_context])
        self.assertIsNone(scenario['options'])

    def test__change_node_names_options_server_name_empty(self):
        ctx_attrs = {
            'name': 'demo',
            'task_id': '1234567890'
        }

        my_context = dummy.DummyContext()
        my_context.init(ctx_attrs)
        scenario = copy.deepcopy(self.scenario)
        scenario['options']['server_name'] = None

        self.parser._change_node_names(scenario, [my_context])
        self.assertIsNone(scenario['options']['server_name'])

    def test__parse_tasks(self):
        task_obj = task.Task()
        _uuid = uuid.uuid4()
        task_obj.task_id = _uuid
        task_files = ['/directory/task_file_name.yml']
        mock_parser = mock.Mock()
        mock_parser.parse_task.return_value = {'rendered': 'File content'}
        mock_args = mock.Mock()
        mock_args.render_only = False

        tasks = task_obj._parse_tasks(mock_parser, task_files, mock_args,
                                      ['arg1'], ['file_arg1'])
        self.assertEqual(
            [{'rendered': 'File content', 'case_name': 'task_file_name'}],
            tasks)
        mock_parser.parse_task.assert_called_once_with(
            _uuid, 'arg1', 'file_arg1')

    @mock.patch.object(sys, 'exit')
    @mock.patch.object(utils, 'write_file')
    @mock.patch.object(utils, 'makedirs')
    def test__parse_tasks_render_only(self, mock_makedirs, mock_write_file,
                                      mock_exit):
        task_obj = task.Task()
        _uuid = uuid.uuid4()
        task_obj.task_id = _uuid
        task_files = ['/directory/task_file_name.yml']
        mock_parser = mock.Mock()
        mock_parser.parse_task.return_value = {'rendered': 'File content'}
        mock_args = mock.Mock()
        mock_args.render_only = '/output_directory'

        task_obj._parse_tasks(mock_parser, task_files, mock_args,
                              ['arg1'], ['file_arg1'])
        mock_makedirs.assert_called_once_with('/output_directory')
        mock_write_file.assert_called_once_with(
            '/output_directory/000-task_file_name.yml', 'File content')
        mock_exit.assert_called_once_with(0)

    def test__render_task_no_args(self):
        task_parser = task.TaskParser('task_file')
        task_str = io.StringIO(six.text_type(self.TASK))
        with mock.patch.object(six.moves.builtins, 'open',
                               return_value=task_str) as mock_open:
            parsed, rendered = task_parser._render_task(None, None)

        self.assertEqual(self.TASK_RENDERED_1, rendered)
        self.assertEqual({'key1': 'var1', 'key2': ['var2']}, parsed)
        mock_open.assert_called_once_with('task_file')

    def test__render_task_arguments(self):
        task_parser = task.TaskParser('task_file')
        task_str = io.StringIO(six.text_type(self.TASK))
        with mock.patch.object(six.moves.builtins, 'open',
                               return_value=task_str) as mock_open:
            parsed, rendered = task_parser._render_task('value1: "var1"', None)

        self.assertEqual(self.TASK_RENDERED_1, rendered)
        self.assertEqual({'key1': 'var1', 'key2': ['var2']}, parsed)
        mock_open.assert_called_once_with('task_file')

    def test__render_task_file_arguments(self):
        task_parser = task.TaskParser('task_file')
        with mock.patch.object(six.moves.builtins, 'open') as mock_open:
            mock_open.side_effect = (
                io.StringIO(six.text_type('value2: var4')),
                io.StringIO(six.text_type(self.TASK))
            )
            parsed, rendered = task_parser._render_task('value1: "var3"',
                                                        'args_file')

        self.assertEqual(self.TASK_RENDERED_2, rendered)
        self.assertEqual({'key1': 'var3', 'key2': ['var4']}, parsed)
        mock_open.assert_has_calls([mock.call('args_file'),
                                    mock.call('task_file')])

    def test__render_task_error_arguments(self):
        with self.assertRaises(exceptions.TaskRenderArgumentError):
            task.TaskParser('task_file')._render_task('value1="var3"', None)

    def test__render_task_error_task_file(self):
        task_parser = task.TaskParser('task_file')
        with mock.patch.object(six.moves.builtins, 'open') as mock_open:
            mock_open.side_effect = (
                io.StringIO(six.text_type('value2: var4')),
                IOError()
            )
            with self.assertRaises(exceptions.TaskReadError):
                task_parser._render_task('value1: "var3"', 'args_file')

        mock_open.assert_has_calls([mock.call('args_file'),
                                    mock.call('task_file')])

    def test__render_task_render_error(self):
        task_parser = task.TaskParser('task_file')
        with mock.patch.object(six.moves.builtins, 'open') as mock_open, \
                mock.patch.object(task_template.TaskTemplate, 'render',
                                  side_effect=TypeError) as mock_render:
            mock_open.side_effect = (
                io.StringIO(six.text_type('value2: var4')),
                io.StringIO(six.text_type(self.TASK))
            )
            with self.assertRaises(exceptions.TaskRenderError):
                task_parser._render_task('value1: "var3"', 'args_file')

        mock_open.assert_has_calls([mock.call('args_file'),
                                    mock.call('task_file')])
        mock_render.assert_has_calls(
            [mock.call(self.TASK, value1='var3', value2='var4')])
