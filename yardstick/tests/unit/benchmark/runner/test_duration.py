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
import time

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

    @mock.patch.object(os, 'getpid')
    def test__worker_process_runner_id(self, mock_os_getpid):
        scenario_cfg = {
            'runner': {'duration': 0}
        }

        mock_os_getpid.return_value = 101
        my_benchmark = mock.Mock()
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        _worker_process(mock.Mock(), my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(), mock.Mock())

        self.assertEqual(scenario_cfg['runner']['runner_id'], 101)

    def test__worker_process_called_with_cfg(self):
        scenario_cfg = {
            'runner': {'interval': 0,
                       'duration': 0}
        }

        my_benchmark = mock.Mock()
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        _worker_process(mock.Mock(), my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(), mock.Mock())

        my_benchmark_cls.assert_called_once_with(scenario_cfg, {})
        my_benchmark.setup.assert_called_once()
        my_benchmark.pre_run_wait_time.assert_called_once_with(0)
        my_benchmark.my_method.assert_called_once_with({})
        my_benchmark.post_run_wait_time.assert_called_once_with(0)
        my_benchmark.teardown.assert_called_once()

    def test__worker_process_called_with_cfg_loop(self):
        scenario_cfg = {
            'runner': {'interval': 0,
                       'duration': 0.01}
        }

        my_benchmark = mock.Mock()
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        _worker_process(mock.Mock(), my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(), mock.Mock())

        my_benchmark_cls.assert_called_once_with(scenario_cfg, {})
        my_benchmark.setup.assert_called_once()
        self.assertGreater(my_benchmark.pre_run_wait_time.call_count, 1)
        self.assertGreater(my_benchmark.my_method.call_count, 1)
        self.assertGreater(my_benchmark.post_run_wait_time.call_count, 1)
        my_benchmark.teardown.assert_called_once()

    def test__worker_process_called_without_cfg(self):
        scenario_cfg = {
            'runner': {}
        }
        aborted = multiprocessing.Event()
        aborted.set()

        my_benchmark = mock.Mock()
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        _worker_process(mock.Mock(), my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, aborted, mock.Mock())

        my_benchmark_cls.assert_called_once_with(scenario_cfg, {})
        my_benchmark.setup.assert_called_once()
        my_benchmark.pre_run_wait_time.assert_called_once_with(1)
        my_benchmark.my_method.assert_called_once_with({})
        my_benchmark.post_run_wait_time.assert_called_once_with(1)
        my_benchmark.teardown.assert_called_once()

    def test__worker_process_output_queue(self):
        scenario_cfg = {
            'runner': {'duration': 0},
        }

        output_queue = multiprocessing.Queue()
        my_benchmark = mock.Mock()
        my_benchmark.my_method = mock.Mock(return_value='my_result')
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        _worker_process(mock.Mock(), my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(),
                        output_queue)

        self.assertEquals(output_queue.get(), 'my_result')

    def test__worker_process_output_queue_multiple_iterations(self):
        class MyMethod(object):
            def __init__(self):
                self.count = 0

            def __call__(self, *args, **kwargs):
                self.count += 1
                return self.count

        scenario_cfg = {
            'runner': {'duration': 0.01},
        }

        output_queue = multiprocessing.Queue()
        my_benchmark = mock.Mock()
        my_benchmark.my_method = MyMethod()
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        _worker_process(mock.Mock(), my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(),
                        output_queue)

        count = 0
        while not output_queue.empty():
            count += 1
            self.assertEquals(output_queue.get(), count)

    def test__worker_process_queue(self):
        def my_method(data):
            data['my_key'] = 'my_value'

        scenario_cfg = {
            'runner': {'duration': 0},
        }

        queue = multiprocessing.Queue()
        my_benchmark = mock.Mock()
        my_benchmark.my_method = my_method
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        start_time = time.time()
        _worker_process(queue, my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        result = queue.get()
        self.assertGreater(result['timestamp'], start_time)
        self.assertEqual(result['errors'], '')
        self.assertEqual(result['data'], {'my_key': 'my_value'})
        self.assertEqual(result['sequence'], 1)

    def test__worker_process_queue_multiple_iterations(self):
        class MyMethod(object):
            def __init__(self):
                self.count = 0

            def __call__(self, data):
                self.count += 1
                data['my_key'] = self.count

        scenario_cfg = {
            'runner': {'duration': 0.01},
        }

        queue = multiprocessing.Queue()
        my_benchmark = mock.Mock()
        my_benchmark.my_method = MyMethod()
        my_benchmark_cls = mock.Mock(return_value=my_benchmark)

        start_time = time.time()
        _worker_process(queue, my_benchmark_cls, 'my_method',
                        scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        count = 0
        while not queue.empty():
            count += 1
            result = queue.get()
            self.assertGreater(result['timestamp'], start_time)
            self.assertEqual(result['errors'], '')
            self.assertEqual(result['data'], {'my_key': count})
            self.assertEqual(result['sequence'], count)
