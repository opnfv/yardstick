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
import subprocess

from yardstick.benchmark.runners import base as runner_base
from yardstick.benchmark.runners import iteration
from yardstick.tests.unit import base as ut_base


class ActionTestCase(ut_base.BaseUnitTestCase):

    def setUp(self):
        self._mock_log = mock.patch.object(runner_base.log, 'error')
        self.mock_log = self._mock_log.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_log.stop()

    @mock.patch.object(subprocess, 'check_output')
    def test__execute_shell_command(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(-1, '')
        self.assertEqual(runner_base._execute_shell_command("")[0], -1)

    @mock.patch.object(subprocess, 'check_output')
    def test__single_action(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(-1, '')
        runner_base._single_action(0, 'echo', mock.Mock())

    @mock.patch.object(subprocess, 'check_output')
    def test__periodic_action(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(-1, '')
        runner_base._periodic_action(0, 'echo', mock.Mock())


class RunnerTestCase(ut_base.BaseUnitTestCase):

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
        runner = runner_base.Runner(mock.Mock())

        with self.assertRaises(NotImplementedError):
            runner._run_benchmark(mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock())
