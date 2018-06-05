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
    class BroadException(Exception):
        pass

    def setUp(self):
        self.scenario_cfg = {
            'runner': {'interval': 0, "duration": 0},
            'type': 'some_type'
        }

        self.benchmark = mock.Mock()
        self.benchmark_cls = mock.Mock(return_value=self.benchmark)

    def _assert_defaults__worker_run_setup_and_teardown(self):
        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.teardown.assert_called_once()

    def _assert_defaults__worker_run_one_iteration(self):
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.my_method.assert_called_once_with({})
        self.benchmark.post_run_wait_time.assert_called_once_with(0)

    @mock.patch.object(os, 'getpid')
    @mock.patch.object(multiprocessing, 'Process')
    def test__run_benchmark_called_with(self, mock_multiprocessing_process,
                                        mock_os_getpid):
        mock_os_getpid.return_value = 101

        runner = DurationRunner({})
        benchmark_cls = mock.Mock()
        runner._run_benchmark(benchmark_cls, 'my_method', self.scenario_cfg,
                              {})
        mock_multiprocessing_process.assert_called_once_with(
            name='Duration-some_type-101',
            target=_worker_process,
            args=(runner.result_queue, benchmark_cls, 'my_method',
                  self.scenario_cfg, {}, runner.aborted, runner.output_queue))

    @mock.patch.object(os, 'getpid')
    def test__worker_process_runner_id(self, mock_os_getpid):
        mock_os_getpid.return_value = 101

        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self.assertEqual(self.scenario_cfg['runner']['runner_id'], 101)

    def test__worker_process_called_with_cfg(self):
        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self._assert_defaults__worker_run_one_iteration()

    def test__worker_process_called_with_cfg_loop(self):
        self.scenario_cfg['runner']['duration'] = 0.01

        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self.assertGreater(self.benchmark.pre_run_wait_time.call_count, 2)
        self.assertGreater(self.benchmark.my_method.call_count, 2)
        self.assertGreater(self.benchmark.post_run_wait_time.call_count, 2)

    def test__worker_process_called_without_cfg(self):
        scenario_cfg = {'runner': {}}
        aborted = multiprocessing.Event()
        aborted.set()

        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        scenario_cfg, {}, aborted, mock.Mock())

        self.benchmark_cls.assert_called_once_with(scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.pre_run_wait_time.assert_called_once_with(1)
        self.benchmark.my_method.assert_called_once_with({})
        self.benchmark.post_run_wait_time.assert_called_once_with(1)
        self.benchmark.teardown.assert_called_once()

    def test__worker_process_output_queue(self):
        self.benchmark.my_method = mock.Mock(return_value='my_result')

        output_queue = multiprocessing.Queue()
        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        output_queue)

        self._assert_defaults__worker_run_setup_and_teardown()
        self._assert_defaults__worker_run_one_iteration()
        self.assertEquals(output_queue.get(), 'my_result')

    def test__worker_process_output_queue_multiple_iterations(self):
        class MyMethod(object):
            def __init__(self):
                self.count = 101

            def __call__(self, *args, **kwargs):
                self.count += 1
                return self.count

        self.scenario_cfg['runner']['duration'] = 0.01
        self.benchmark.my_method = MyMethod()

        output_queue = multiprocessing.Queue()
        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        output_queue)

        self._assert_defaults__worker_run_setup_and_teardown()
        self.assertGreater(self.benchmark.pre_run_wait_time.call_count, 2)
        self.assertGreater(self.benchmark.my_method.count, 103)
        self.assertGreater(self.benchmark.post_run_wait_time.call_count, 2)

        count = 101
        while not output_queue.empty():
            count += 1
            self.assertEquals(output_queue.get(), count)

    def test__worker_process_queue(self):
        def my_method(data):
            data['my_key'] = 'my_value'

        self.benchmark.my_method = my_method

        queue = multiprocessing.Queue()
        start_time = time.time()
        _worker_process(queue, self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.post_run_wait_time.assert_called_once_with(0)

        result = queue.get()
        self.assertGreater(result['timestamp'], start_time)
        self.assertEqual(result['errors'], '')
        self.assertEqual(result['data'], {'my_key': 'my_value'})
        self.assertEqual(result['sequence'], 1)

    def test__worker_process_queue_multiple_iterations(self):
        class MyMethod(object):
            def __init__(self):
                self.count = 101

            def __call__(self, data):
                self.count += 1
                data['my_key'] = self.count

        self.scenario_cfg['runner']['duration'] = 0.01
        self.benchmark.my_method = MyMethod()

        queue = multiprocessing.Queue()
        start_time = time.time()
        _worker_process(queue, self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self.assertGreater(self.benchmark.pre_run_wait_time.call_count, 2)
        self.assertGreater(self.benchmark.my_method.count, 103)
        self.assertGreater(self.benchmark.post_run_wait_time.call_count, 2)

        iteration = 0
        count = 101
        while not queue.empty():
            iteration += 1
            count += 1
            result = queue.get()
            self.assertGreater(result['timestamp'], start_time)
            self.assertEqual(result['errors'], '')
            self.assertEqual(result['data'], {'my_key': count})
            self.assertEqual(result['sequence'], iteration)

    def test__worker_process_except_assertionerror_no_sla_cfg(self):
        self.benchmark.my_method = mock.Mock(side_effect=AssertionError)

        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self._assert_defaults__worker_run_one_iteration()

    def test__worker_process_raise_assertionerror_sla_cfg_default(self):
        self.scenario_cfg['sla'] = {}
        self.benchmark.my_method = mock.Mock(side_effect=AssertionError)

        with self.assertRaises(AssertionError):
            _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                            self.scenario_cfg, {}, multiprocessing.Event(),
                            mock.Mock())

        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.my_method.assert_called_once_with({})

    def test__worker_process_raise_assertionerror_sla_cfg(self):
        self.scenario_cfg['sla'] = {'action': 'assert'}
        self.benchmark.my_method = mock.Mock(side_effect=AssertionError)

        with self.assertRaises(AssertionError):
            _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                            self.scenario_cfg, {}, multiprocessing.Event(),
                            mock.Mock())

        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.my_method.assert_called_once_with({})

    def test__worker_process_ok_sla_cfg_monitor(self):
        self.scenario_cfg['sla'] = {'action': 'monitor'}
        self.benchmark.my_method = mock.Mock(side_effect=AssertionError)

        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self._assert_defaults__worker_run_one_iteration()

    def test__worker_process_queue_on_sla_error_monitor(self):
        def my_method(data):
            data['my_key'] = 'my_value'
            raise AssertionError('my_SLA_error')

        self.scenario_cfg['sla'] = {'action': 'monitor'}
        self.benchmark.my_method = my_method

        queue = multiprocessing.Queue()
        start_time = time.time()
        _worker_process(queue, self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.post_run_wait_time.assert_called_once_with(0)

        result = queue.get()
        self.assertGreater(result['timestamp'], start_time)
        self.assertEqual(result['errors'], ('my_SLA_error',))
        self.assertEqual(result['data'], {'my_key': 'my_value'})
        self.assertEqual(result['sequence'], 1)

    def test__worker_process_broad_exception(self):
        self.benchmark.my_method = mock.Mock(side_effect=self.BroadException)

        _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self._assert_defaults__worker_run_one_iteration()

    def test__worker_process_queue_on_broad_exception(self):
        def my_method(data):
            data['my_key'] = 'my_value'
            raise self.BroadException

        self.benchmark.my_method = my_method

        queue = multiprocessing.Queue()
        start_time = time.time()
        _worker_process(queue, self.benchmark_cls, 'my_method',
                        self.scenario_cfg, {}, multiprocessing.Event(),
                        mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self.benchmark.pre_run_wait_time.assert_called_once_with(0)
        self.benchmark.post_run_wait_time.assert_called_once_with(0)

        result = queue.get()
        self.assertGreater(result['timestamp'], start_time)
        self.assertNotEqual(result['errors'], '')
        self.assertEqual(result['data'], {'my_key': 'my_value'})
        self.assertEqual(result['sequence'], 1)

    def test__worker_process_benchmark_teardown_on_broad_exception(self):
        self.benchmark.teardown = mock.Mock(side_effect=self.BroadException)

        with self.assertRaises(SystemExit) as raised:
            _worker_process(mock.Mock(), self.benchmark_cls, 'my_method',
                            self.scenario_cfg, {}, multiprocessing.Event(),
                            mock.Mock())
        self.assertEqual(raised.exception.code, 1)
        self._assert_defaults__worker_run_setup_and_teardown()
        self._assert_defaults__worker_run_one_iteration()
