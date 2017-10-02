#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import unittest
import time

from mock import mock

from yardstick.benchmark.runners import base
from yardstick.benchmark.runners.iteration import IterationRunner


class ActionTestCase(unittest.TestCase):

    @mock.patch("yardstick.benchmark.runners.base.subprocess")
    def test__execute_shell_command(self, mock_subprocess):
        mock_subprocess.check_output.side_effect = Exception()

        self.assertEqual(base._execute_shell_command("")[0], -1)

    @mock.patch("yardstick.benchmark.runners.base.subprocess")
    def test__single_action(self, mock_subprocess):
        mock_subprocess.check_output.side_effect = Exception()

        base._single_action(0, "echo", mock.MagicMock())

    @mock.patch("yardstick.benchmark.runners.base.subprocess")
    def test__periodic_action(self, mock_subprocess):
        mock_subprocess.check_output.side_effect = Exception()

        base._periodic_action(0, "echo", mock.MagicMock())


class RunnerTestCase(unittest.TestCase):

    @mock.patch("yardstick.benchmark.runners.iteration.multiprocessing")
    def test_get_output(self, mock_process):
        runner = IterationRunner({})
        runner.output_queue.put({'case': 'opnfv_yardstick_tc002'})
        runner.output_queue.put({'criteria': 'PASS'})

        idle_result = {
            'case': 'opnfv_yardstick_tc002',
            'criteria': 'PASS'
        }

        for retries in range(1000):
            time.sleep(0.01)
            if not runner.output_queue.empty():
                break
        actual_result = runner.get_output()
        self.assertEqual(idle_result, actual_result)

    @mock.patch("yardstick.benchmark.runners.iteration.multiprocessing")
    def test_get_result(self, mock_process):
        runner = IterationRunner({})
        runner.result_queue.put({'case': 'opnfv_yardstick_tc002'})
        runner.result_queue.put({'criteria': 'PASS'})

        idle_result = [
            {'case': 'opnfv_yardstick_tc002'},
            {'criteria': 'PASS'}
        ]

        for retries in range(1000):
            time.sleep(0.01)
            if not runner.result_queue.empty():
                break
        actual_result = runner.get_result()
        self.assertEqual(idle_result, actual_result)

    def test__run_benchmark(self):
        runner = base.Runner(mock.Mock())

        with self.assertRaises(NotImplementedError):
            runner._run_benchmark(mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock())


def main():
    unittest.main()


if __name__ == '__main__':
    main()
