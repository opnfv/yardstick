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

from yardstick.benchmark.runners.duration import DurationRunner
from yardstick.benchmark.runners.duration import _worker_process


class DurationRunnerTest(unittest.TestCase):

    @mock.patch.object(multiprocessing, 'Process')
    def test__run_benchmark(self, mock_multiprocessing_process):
        scenario_cfg = {
            'runner': {},
        }

        runner = DurationRunner({})
        runner._run_benchmark(mock.Mock(), 'my_method', scenario_cfg, {})
        mock_multiprocessing_process.assert_called_once()
        runner.process.start.assert_called_once()

    @mock.patch.object(os, 'getpid')
    @mock.patch.object(multiprocessing, 'Process')
    def test__run_benchmark_called_with(self, mock_multiprocessing_process,
                                        mock_os_getpid):
        scenario_cfg = {
            'runner': {},
            'type': 'some_type'
        }
        mock_os_getpid.return_value = 101

        runner = DurationRunner({})
        benchmark_cls = mock.Mock()
        runner._run_benchmark(benchmark_cls, 'my_method', scenario_cfg, {})
        mock_multiprocessing_process.assert_called_once_with(
            name='Duration-some_type-101',
            target=_worker_process,
            args=(runner.result_queue, benchmark_cls, 'my_method',
                  scenario_cfg, {}, runner.aborted, runner.output_queue))
