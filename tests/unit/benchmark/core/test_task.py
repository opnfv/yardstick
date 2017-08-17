#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.core.task

from __future__ import print_function

from __future__ import absolute_import
import os
import unittest

try:
    from unittest import mock
except ImportError:
    import mock


from yardstick.benchmark.core import task
from yardstick.common import constants as consts


class TaskTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.core.task.Context')
    def test_parse_nodes_host_target_same_context(self, mock_context):
        nodes = {
            "host": "node1.LF",
            "target": "node2.LF"
        }
        scenario_cfg = {"nodes": nodes}
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

    @mock.patch('yardstick.benchmark.core.task.DispatcherBase')
    def test__do_output(self, mock_dispatcher):
        t = task.Task()
        output_config = {"DEFAULT": {"dispatcher": "file, http"}}
        mock_dispatcher.get = mock.MagicMock(return_value=[mock.MagicMock(),
                                                           mock.MagicMock()])
        self.assertEqual(None, t._do_output(output_config, {}))

    @mock.patch('yardstick.benchmark.core.task.Context')
    def test_parse_networks_from_nodes(self, mock_context):
        nodes = {
            'node1': {
                'interfaces': {
                    'eth0': {
                        'name': 'mgmt',
                    },
                    'eth1': {
                        'name': 'external',
                        'vld_id': '23',
                    },
                    'eth10': {
                        'name': 'internal',
                        'vld_id': '55',
                    },
                },
            },
            'node2': {
                'interfaces': {
                    'eth4': {
                        'name': 'mgmt',
                    },
                    'eth2': {
                        'name': 'external',
                        'vld_id': '32',
                    },
                    'eth11': {
                        'name': 'internal',
                        'vld_id': '55',
                    },
                },
            },
        }

        mock_context.get_network.side_effect = iter([
            None,
            {
                'name': 'a',
                'network_type': 'private',
            },
            {},
            {
                'name': 'b',
                'vld_id': 'y',
                'subnet_cidr': '10.20.0.0/16',
            },
            {
                'name': 'c',
                'vld_id': 'x',
            },
            {
                'name': 'd',
                'vld_id': 'w',
            },
        ])

        # once for each vld_id in the nodes dict
        expected_get_network_calls = 4
        expected = {
            'a': {'name': 'a', 'network_type': 'private'},
            'b': {'name': 'b', 'vld_id': 'y', 'subnet_cidr': '10.20.0.0/16'},
        }

        networks = task.get_networks_from_nodes(nodes)
        self.assertEqual(mock_context.get_network.call_count, expected_get_network_calls)
        self.assertDictEqual(networks, expected)

    @mock.patch('yardstick.benchmark.core.task.Context')
    @mock.patch('yardstick.benchmark.core.task.base_runner')
    def test_run(self, mock_base_runner, mock_ctx):
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
        self.assertTrue(runner.run.called)

    @mock.patch('yardstick.benchmark.core.task.os')
    def test_check_precondition(self, mock_os):
        cfg = {
            'precondition': {
                'installer_type': 'compass',
                'deploy_scenarios': 'os-nosdn',
                'pod_name': 'huawei-pod1'
            }
        }

        t = task.TaskParser('/opt')
        mock_os.environ.get.side_effect = ['compass',
                                           'os-nosdn',
                                           'huawei-pod1']
        result = t._check_precondition(cfg)
        self.assertTrue(result)

    @mock.patch('yardstick.benchmark.core.task.os.environ')
    def test_parse_suite_no_constraint_no_args(self, mock_environ):
        SAMPLE_SCENARIO_PATH = "no_constraint_no_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        mock_environ.get.side_effect = ['huawei-pod1', 'compass']
        task_files, task_args, task_args_fnames = t.parse_suite()
        print("files=%s, args=%s, fnames=%s" % (task_files, task_args,
                                                task_args_fnames))
        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertEqual(task_args[0], None)
        self.assertEqual(task_args[1], None)
        self.assertEqual(task_args_fnames[0], None)
        self.assertEqual(task_args_fnames[1], None)

    @mock.patch('yardstick.benchmark.core.task.os.environ')
    def test_parse_suite_no_constraint_with_args(self, mock_environ):
        SAMPLE_SCENARIO_PATH = "no_constraint_with_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        mock_environ.get.side_effect = ['huawei-pod1', 'compass']
        task_files, task_args, task_args_fnames = t.parse_suite()
        print("files=%s, args=%s, fnames=%s" % (task_files, task_args,
                                                task_args_fnames))
        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertEqual(task_args[0], None)
        self.assertEqual(task_args[1],
                         '{"host": "node1.LF","target": "node2.LF"}')
        self.assertEqual(task_args_fnames[0], None)
        self.assertEqual(task_args_fnames[1], None)

    @mock.patch('yardstick.benchmark.core.task.os.environ')
    def test_parse_suite_with_constraint_no_args(self, mock_environ):
        SAMPLE_SCENARIO_PATH = "with_constraint_no_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        mock_environ.get.side_effect = ['huawei-pod1', 'compass']
        task_files, task_args, task_args_fnames = t.parse_suite()
        print("files=%s, args=%s, fnames=%s" % (task_files, task_args,
                                                task_args_fnames))
        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertEqual(task_args[0], None)
        self.assertEqual(task_args[1], None)
        self.assertEqual(task_args_fnames[0], None)
        self.assertEqual(task_args_fnames[1], None)

    @mock.patch('yardstick.benchmark.core.task.os.environ')
    def test_parse_suite_with_constraint_with_args(self, mock_environ):
        SAMPLE_SCENARIO_PATH = "with_constraint_with_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        mock_environ.get.side_effect = ['huawei-pod1', 'compass']
        task_files, task_args, task_args_fnames = t.parse_suite()
        print("files=%s, args=%s, fnames=%s" % (task_files, task_args,
                                                task_args_fnames))
        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertEqual(task_args[0], None)
        self.assertEqual(task_args[1],
                         '{"host": "node1.LF","target": "node2.LF"}')
        self.assertEqual(task_args_fnames[0], None)
        self.assertEqual(task_args_fnames[1], None)

    def test_parse_options(self):
        options = {
            'openstack': {
                'EXTERNAL_NETWORK': '$network'
            },
            'ndoes': ['node1', '$node'],
            'host': '$host'
        }

        t = task.Task()
        t.outputs = {
            'network': 'ext-net',
            'node': 'node2',
            'host': 'server.yardstick'
        }

        idle_result = {
            'openstack': {
                'EXTERNAL_NETWORK': 'ext-net'
            },
            'ndoes': ['node1', 'node2'],
            'host': 'server.yardstick'
        }

        actual_result = t._parse_options(options)
        self.assertEqual(idle_result, actual_result)

    def test_change_server_name_host_str(self):
        scenario = {'host': 'demo'}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertTrue(scenario['host'], 'demo-8')

    def test_change_server_name_host_dict(self):
        scenario = {'host': {'name': 'demo'}}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertTrue(scenario['host']['name'], 'demo-8')

    def test_change_server_name_target_str(self):
        scenario = {'target': 'demo'}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertTrue(scenario['target'], 'demo-8')

    def test_change_server_name_target_dict(self):
        scenario = {'target': {'name': 'demo'}}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertTrue(scenario['target']['name'], 'demo-8')

    @mock.patch('yardstick.benchmark.core.task.utils')
    @mock.patch('yardstick.benchmark.core.task.logging')
    def test_set_log(self, mock_logging, mock_utils):
        task_obj = task.Task()
        task_obj.task_id = 'task_id'
        task_obj._set_log()
        self.assertTrue(mock_logging.root.addHandler.called)

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def change_to_abspath(self, filepath):
        return os.path.join(consts.YARDSTICK_ROOT_PATH, filepath)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
