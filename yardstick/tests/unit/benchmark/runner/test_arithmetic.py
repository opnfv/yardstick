##############################################################################
# Copyright (c) 2018 Nokia and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest
import multiprocessing
import os

from yardstick.benchmark.runners import arithmetic


class ArithmeticRunnerTest(unittest.TestCase):
    def setUp(self):
        self.scenario_cfg = {
            'type': 'some_type'
        }

    @mock.patch.object(os, 'getpid')
    @mock.patch.object(multiprocessing, 'Process')
    def test__run_benchmark_called_with(self, mock_multiprocessing_process,
                                        mock_os_getpid):
        mock_os_getpid.return_value = 101

        runner = arithmetic.ArithmeticRunner({})
        benchmark_cls = mock.Mock()
        runner._run_benchmark(benchmark_cls, 'my_method', self.scenario_cfg,
                              {})
        mock_multiprocessing_process.assert_called_once_with(
            name='Arithmetic-some_type-101',
            target=arithmetic._worker_process,
            args=(runner.result_queue, benchmark_cls, 'my_method',
                  self.scenario_cfg, {}, runner.aborted, runner.output_queue))
