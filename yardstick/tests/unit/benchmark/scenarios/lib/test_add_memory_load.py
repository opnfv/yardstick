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

from yardstick.benchmark.scenarios.lib.add_memory_load import AddMemoryLoad


class AddMemoryLoadTestCase(unittest.TestCase):

    @mock.patch('yardstick.ssh.SSH.from_node')
    def test_add_memory_load_with_load(self, mock_from_node):
        scenario_cfg = {
            'options': {
                'memory_load': 0.5
            }
        }
        context_cfg = {
            'host': {}
        }
        mock_from_node().execute.return_value = (0, '0 2048 512', '')
        obj = AddMemoryLoad(scenario_cfg, context_cfg)
        obj.run({})
        self.assertTrue(mock_from_node.called)

    @mock.patch('yardstick.ssh.SSH.from_node')
    def test_add_memory_load_without_load(self, mock_from_node):
        scenario_cfg = {
            'options': {
                'memory_load': 0
            }
        }
        context_cfg = {
            'host': {}
        }
        obj = AddMemoryLoad(scenario_cfg, context_cfg)
        obj.run({})
        self.assertTrue(mock_from_node.called)

    @mock.patch('yardstick.ssh.SSH.from_node')
    def test_add_memory_load_without_args(self, mock_from_node):
        scenario_cfg = {
            'options': {
            }
        }
        context_cfg = {
            'host': {}
        }
        obj = AddMemoryLoad(scenario_cfg, context_cfg)
        obj.run({})
        self.assertTrue(mock_from_node.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
