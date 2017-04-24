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

from yardstick.benchmark.runners.base import Runner
from yardstick.benchmark.runners.iteration import IterationRunner


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

    def test__run_benchmark(self):
        runner = Runner(mock.Mock())

        with self.assertRaises(NotImplementedError):
            runner._run_benchmark(mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock())


def main():
    unittest.main()


if __name__ == '__main__':
    main()
