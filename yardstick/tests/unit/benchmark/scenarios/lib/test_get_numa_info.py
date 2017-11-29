##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import mock

from yardstick.benchmark.scenarios.lib.get_numa_info import GetNumaInfo

BASE = 'yardstick.benchmark.scenarios.lib.get_numa_info'


class GetNumaInfoTestCase(unittest.TestCase):

    @mock.patch('{}.GetNumaInfo._check_numa_node'.format(BASE))
    @mock.patch('{}.GetNumaInfo._get_current_host_name'.format(BASE))
    @mock.patch('yardstick.benchmark.scenarios.lib.get_numa_info.yaml_load')
    @mock.patch('yardstick.common.task_template.TaskTemplate.render')
    def test_get_numa_info(self,
                           mock_render,
                           mock_safe_load,
                           mock_get_current_host_name,
                           mock_check_numa_node):
        scenario_cfg = {
            'options': {
                'server': {
                    'id': '1'
                },
                'file': 'yardstick/ssh.py'
            },
            'output': 'numa_info'
        }
        mock_safe_load.return_value = {
            'nodes': []
        }
        obj = GetNumaInfo(scenario_cfg, {})
        obj.run({})
        self.assertTrue(mock_get_current_host_name.called)
        self.assertTrue(mock_check_numa_node.called)

    @mock.patch('yardstick.ssh.SSH.from_node')
    @mock.patch('{}.GetNumaInfo._get_current_host_name'.format(BASE))
    @mock.patch('yardstick.benchmark.scenarios.lib.get_numa_info.yaml_load')
    @mock.patch('yardstick.common.task_template.TaskTemplate.render')
    def test_check_numa_node(self,
                             mock_render,
                             mock_safe_load,
                             mock_get_current_host_name,
                             mock_from_node):
        scenario_cfg = {
            'options': {
                'server': {
                    'id': '1'
                },
                'file': 'yardstick/ssh.py'
            },
            'output': 'numa_info'
        }
        mock_safe_load.return_value = {
            'nodes': []
        }
        data = """
        <data>
        </data>
        """
        mock_from_node().execute.return_value = (0, data, '')
        obj = GetNumaInfo(scenario_cfg, {})
        result = obj._check_numa_node('1', 'host4')
        self.assertEqual(result, {'pinning': [], 'vcpupin': []})

    @mock.patch('{}.change_obj_to_dict'.format(BASE))
    @mock.patch('{}.get_nova_client'.format(BASE))
    @mock.patch('yardstick.benchmark.scenarios.lib.get_numa_info.yaml_load')
    @mock.patch('yardstick.common.task_template.TaskTemplate.render')
    def test_get_current_host_name(self,
                                   mock_render,
                                   mock_safe_load,
                                   mock_get_nova_client,
                                   mock_change_obj_to_dict):
        scenario_cfg = {
            'options': {
                'server': {
                    'id': '1'
                },
                'file': 'yardstick/ssh.py'
            },
            'output': 'numa_info'
        }
        mock_get_nova_client().servers.get.return_value = ''
        mock_change_obj_to_dict.return_value = {'OS-EXT-SRV-ATTR:host': 'host5'}

        obj = GetNumaInfo(scenario_cfg, {})
        result = obj._get_current_host_name('1')
        self.assertEqual(result, 'host5')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
