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

from yardstick.benchmark.runners import arithmetic
from yardstick.common import exceptions as y_exc


class ArithmeticRunnerTest(unittest.TestCase):
    class MyMethod(object):
        SLA_VALIDATION_ERROR_SIDE_EFFECT = 1
        BROAD_EXCEPTION_SIDE_EFFECT = 2

        def __init__(self, side_effect=0):
            self.count = 101
            self.side_effect = side_effect

        def __call__(self, data):
            self.count += 1
            data['my_key'] = self.count
            if self.side_effect == self.SLA_VALIDATION_ERROR_SIDE_EFFECT:
                raise y_exc.SLAValidationError(case_name='My Case',
                                               error_msg='my error message')
            elif self.side_effect == self.BROAD_EXCEPTION_SIDE_EFFECT:
                raise y_exc.YardstickException
            return self.count

    def setUp(self):
        self.scenario_cfg = {
            'runner': {
                'interval': 0,
                'iter_type': 'nested_for_loops',
                'iterators': [
                    {
                        'name': 'stride',
                        'start': 64,
                        'stop': 128,
                        'step': 64
                    },
                    {
                        'name': 'size',
                        'start': 500,
                        'stop': 2000,
                        'step': 500
                    }
                ]
            },
            'type': 'some_type'
        }

        self.benchmark = mock.Mock()
        self.benchmark_cls = mock.Mock(return_value=self.benchmark)

    def _assert_defaults__worker_process_run_setup_and_teardown(self):
        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.teardown.assert_called_once()

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

    @mock.patch.object(os, 'getpid')
    def test__worker_process_runner_id(self, mock_os_getpid):
        mock_os_getpid.return_value = 101

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self.assertEqual(self.scenario_cfg['runner']['runner_id'], 101)

    @mock.patch.object(time, 'sleep')
    def test__worker_process_calls_nested_for_loops(self, mock_time_sleep):
        self.scenario_cfg['runner']['interval'] = 99

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.benchmark.my_method.assert_has_calls([mock.call({})] * 8)
        self.assertEqual(self.benchmark.my_method.call_count, 8)
        mock_time_sleep.assert_has_calls([mock.call(99)] * 8)
        self.assertEqual(mock_time_sleep.call_count, 8)

    @mock.patch.object(time, 'sleep')
    def test__worker_process_calls_tuple_loops(self, mock_time_sleep):
        self.scenario_cfg['runner']['interval'] = 99
        self.scenario_cfg['runner']['iter_type'] = 'tuple_loops'

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.benchmark.my_method.assert_has_calls([mock.call({})] * 2)
        self.assertEqual(self.benchmark.my_method.call_count, 2)
        mock_time_sleep.assert_has_calls([mock.call(99)] * 2)
        self.assertEqual(mock_time_sleep.call_count, 2)

    def test__worker_process_stored_options_nested_for_loops(self):
        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})

    def test__worker_process_stored_options_tuple_loops(self):
        self.scenario_cfg['runner']['iter_type'] = 'tuple_loops'

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 1000})

    def test__worker_process_aborted_set_early(self):
        aborted = multiprocessing.Event()
        aborted.set()
        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   aborted, mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.scenario_cfg['options'], {})
        self.benchmark.my_method.assert_not_called()

    def test__worker_process_output_queue_nested_for_loops(self):
        self.benchmark.my_method = self.MyMethod()

        output_queue = multiprocessing.Queue()
        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 109)
        result = []
        while not output_queue.empty():
            result.append(output_queue.get())
        self.assertListEqual(result, [102, 103, 104, 105, 106, 107, 108, 109])

    def test__worker_process_output_queue_tuple_loops(self):
        self.scenario_cfg['runner']['iter_type'] = 'tuple_loops'
        self.benchmark.my_method = self.MyMethod()

        output_queue = multiprocessing.Queue()
        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 103)
        result = []
        while not output_queue.empty():
            result.append(output_queue.get())
        self.assertListEqual(result, [102, 103])

    def test__worker_process_queue_nested_for_loops(self):
        self.benchmark.my_method = self.MyMethod()

        queue = multiprocessing.Queue()
        timestamp = time.time()
        arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                   self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 109)
        count = 0
        while not queue.empty():
            count += 1
            result = queue.get()
            self.assertEqual(result['errors'], '')
            self.assertEqual(result['data'], {'my_key': count + 101})
            self.assertEqual(result['sequence'], count)
            self.assertGreater(result['timestamp'], timestamp)
            timestamp = result['timestamp']

    def test__worker_process_queue_tuple_loops(self):
        self.scenario_cfg['runner']['iter_type'] = 'tuple_loops'
        self.benchmark.my_method = self.MyMethod()

        queue = multiprocessing.Queue()
        timestamp = time.time()
        arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                   self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 103)
        count = 0
        while not queue.empty():
            count += 1
            result = queue.get()
            self.assertEqual(result['errors'], '')
            self.assertEqual(result['data'], {'my_key': count + 101})
            self.assertEqual(result['sequence'], count)
            self.assertGreater(result['timestamp'], timestamp)
            timestamp = result['timestamp']

    def test__worker_process_except_sla_validation_error_no_sla_cfg(self):
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.call_count, 8)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})

    def test__worker_process_output_on_sla_validation_error_no_sla_cfg(self):
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.SLA_VALIDATION_ERROR_SIDE_EFFECT)

        queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()
        timestamp = time.time()
        arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                   self.scenario_cfg, {},
                                   multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 109)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})
        count = 0
        while not queue.empty():
            count += 1
            result = queue.get()
            self.assertEqual(result['errors'], '')
            self.assertEqual(result['data'], {'my_key': count + 101})
            self.assertEqual(result['sequence'], count)
            self.assertGreater(result['timestamp'], timestamp)
            timestamp = result['timestamp']
        self.assertEqual(count, 8)
        self.assertTrue(output_queue.empty())

    def test__worker_process_except_sla_validation_error_sla_cfg_monitor(self):
        self.scenario_cfg['sla'] = {'action': 'monitor'}
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.call_count, 8)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})

    def test__worker_process_output_sla_validation_error_sla_cfg_monitor(self):
        self.scenario_cfg['sla'] = {'action': 'monitor'}
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.SLA_VALIDATION_ERROR_SIDE_EFFECT)

        queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()
        timestamp = time.time()
        arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                   self.scenario_cfg, {},
                                   multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 109)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})
        count = 0
        while not queue.empty():
            count += 1
            result = queue.get()
            self.assertEqual(result['errors'],
                             ('My Case SLA validation failed. '
                              'Error: my error message',))
            self.assertEqual(result['data'], {'my_key': count + 101})
            self.assertEqual(result['sequence'], count)
            self.assertGreater(result['timestamp'], timestamp)
            timestamp = result['timestamp']
        self.assertEqual(count, 8)
        self.assertTrue(output_queue.empty())

    def test__worker_process_raise_sla_validation_error_sla_cfg_assert(self):
        self.scenario_cfg['sla'] = {'action': 'assert'}
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)

        with self.assertRaises(y_exc.SLAValidationError):
            arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                       'my_method', self.scenario_cfg, {},
                                       multiprocessing.Event(), mock.Mock())
        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.my_method.assert_called_once()
        self.benchmark.setup.assert_called_once()
        self.benchmark.teardown.assert_not_called()

    def test__worker_process_output_sla_validation_error_sla_cfg_assert(self):
        self.scenario_cfg['sla'] = {'action': 'assert'}
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.SLA_VALIDATION_ERROR_SIDE_EFFECT)

        queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()
        with self.assertRaisesRegexp(
                y_exc.SLAValidationError,
                'My Case SLA validation failed. Error: my error message'):
            arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                       self.scenario_cfg, {},
                                       multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.assertEqual(self.benchmark.my_method.count, 102)
        self.benchmark.teardown.assert_not_called()
        self.assertTrue(queue.empty())
        self.assertTrue(output_queue.empty())

    def test__worker_process_broad_exception_no_sla_cfg_early_exit(self):
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.YardstickException)

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.benchmark.my_method.assert_called_once()
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 64, 'size': 500})

    def test__worker_process_output_on_broad_exception_no_sla_cfg(self):
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.BROAD_EXCEPTION_SIDE_EFFECT)

        queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()
        timestamp = time.time()
        arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                   self.scenario_cfg, {},
                                   multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 102)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 64, 'size': 500})
        self.assertEqual(queue.qsize(), 1)
        result = queue.get()
        self.assertGreater(result['timestamp'], timestamp)
        self.assertEqual(result['data'], {'my_key': 102})
        self.assertRegexpMatches(
            result['errors'],
            'YardstickException: An unknown exception occurred.')
        self.assertEqual(result['sequence'], 1)
        self.assertTrue(output_queue.empty())

    def test__worker_process_broad_exception_sla_cfg_not_none(self):
        self.scenario_cfg['sla'] = {'action': 'some action'}
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.YardstickException)

        arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                   'my_method', self.scenario_cfg, {},
                                   multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.call_count, 8)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})

    def test__worker_process_output_on_broad_exception_sla_cfg_not_none(self):
        self.scenario_cfg['sla'] = {'action': 'some action'}
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.BROAD_EXCEPTION_SIDE_EFFECT)

        queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()
        timestamp = time.time()
        arithmetic._worker_process(queue, self.benchmark_cls, 'my_method',
                                   self.scenario_cfg, {},
                                   multiprocessing.Event(), output_queue)
        time.sleep(0.01)

        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.count, 109)
        self.assertDictEqual(self.scenario_cfg['options'],
                             {'stride': 128, 'size': 2000})
        self.assertTrue(output_queue.empty())
        count = 0
        while not queue.empty():
            count += 1
            result = queue.get()
            self.assertGreater(result['timestamp'], timestamp)
            self.assertEqual(result['data'], {'my_key': count + 101})
            self.assertRegexpMatches(
                result['errors'],
                'YardstickException: An unknown exception occurred.')
            self.assertEqual(result['sequence'], count)

    def test__worker_process_benchmark_teardown_on_broad_exception(self):
        self.benchmark.teardown = mock.Mock(
            side_effect=y_exc.YardstickException)

        with self.assertRaises(SystemExit) as raised:
            arithmetic._worker_process(mock.Mock(), self.benchmark_cls,
                                       'my_method', self.scenario_cfg, {},
                                       multiprocessing.Event(), mock.Mock())
        self.assertEqual(raised.exception.code, 1)
        self._assert_defaults__worker_process_run_setup_and_teardown()
        self.assertEqual(self.benchmark.my_method.call_count, 8)
