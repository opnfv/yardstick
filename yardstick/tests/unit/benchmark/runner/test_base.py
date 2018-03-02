##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import time

import mock
import unittest
from subprocess import CalledProcessError


from yardstick.benchmark.runners import base
from yardstick.benchmark.runners import iteration


class ActionTestCase(unittest.TestCase):

    @mock.patch("yardstick.benchmark.runners.base.subprocess")
    def test__execute_shell_command(self, mock_subprocess):
        mock_subprocess.check_output.side_effect = CalledProcessError(-1, '')

        self.assertEqual(base._execute_shell_command("")[0], -1)

    @mock.patch("yardstick.benchmark.runners.base.subprocess")
    def test__single_action(self, mock_subprocess):
        mock_subprocess.check_output.side_effect = CalledProcessError(-1, '')

        base._single_action(0, "echo", mock.MagicMock())

    @mock.patch("yardstick.benchmark.runners.base.subprocess")
    def test__periodic_action(self, mock_subprocess):
        mock_subprocess.check_output.side_effect = CalledProcessError(-1, '')

        base._periodic_action(0, "echo", mock.MagicMock())


class RunnerTestCase(unittest.TestCase):

    def setUp(self):
        config = {
            'output_config': {
                'DEFAULT': {
                    'dispatcher': 'file'
                }
            }
        }
        self.runner = iteration.IterationRunner(config)

    @mock.patch("yardstick.benchmark.runners.iteration.multiprocessing")
    def test_get_output(self, *args):
        self.runner.output_queue.put({'case': 'opnfv_yardstick_tc002'})
        self.runner.output_queue.put({'criteria': 'PASS'})

        idle_result = {
            'case': 'opnfv_yardstick_tc002',
            'criteria': 'PASS'
        }

        for _ in range(1000):
            time.sleep(0.01)
            if not self.runner.output_queue.empty():
                break
        actual_result = self.runner.get_output()
        self.assertEqual(idle_result, actual_result)

    @mock.patch("yardstick.benchmark.runners.iteration.multiprocessing")
    def test_get_result(self, *args):
        self.runner.result_queue.put({'case': 'opnfv_yardstick_tc002'})
        self.runner.result_queue.put({'criteria': 'PASS'})

        idle_result = [
            {'case': 'opnfv_yardstick_tc002'},
            {'criteria': 'PASS'}
        ]

        for _ in range(1000):
            time.sleep(0.01)
            if not self.runner.result_queue.empty():
                break
        actual_result = self.runner.get_result()
        self.assertEqual(idle_result, actual_result)

    def test__run_benchmark(self):
        runner = base.Runner(mock.Mock())

        with self.assertRaises(NotImplementedError):
            runner._run_benchmark(mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock())
