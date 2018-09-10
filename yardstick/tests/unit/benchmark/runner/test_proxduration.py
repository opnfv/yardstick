# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import unittest
import multiprocessing
import os
import time

from yardstick.benchmark.runners import proxduration
from yardstick.common import constants
from yardstick.common import exceptions as y_exc


class ProxDurationRunnerTest(unittest.TestCase):

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
            'runner': {'interval': 0, "duration": 0},
            'type': 'some_type'
        }

        self.benchmark = mock.Mock()
        self.benchmark_cls = mock.Mock(return_value=self.benchmark)

    def _assert_defaults__worker_run_setup_and_teardown(self):
        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.teardown.assert_called_once()

    @mock.patch.object(os, 'getpid')
    @mock.patch.object(multiprocessing, 'Process')
    def test__run_benchmark_called_with(self, mock_multiprocessing_process,
                                        mock_os_getpid):
        mock_os_getpid.return_value = 101

        runner = proxduration.ProxDurationRunner({})
        benchmark_cls = mock.Mock()
        runner._run_benchmark(benchmark_cls, 'my_method', self.scenario_cfg,
                              {})
        mock_multiprocessing_process.assert_called_once_with(
            name='ProxDuration-some_type-101',
            target=proxduration._worker_process,
            args=(runner.result_queue, benchmark_cls, 'my_method',
                  self.scenario_cfg, {}, runner.aborted, runner.output_queue))

    @mock.patch.object(os, 'getpid')
    def test__worker_process_runner_id(self, mock_os_getpid):
        mock_os_getpid.return_value = 101
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), mock.Mock())

        self.assertEqual(101, self.scenario_cfg['runner']['runner_id'])

    def test__worker_process_called_with_cfg(self):
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()

    def test__worker_process_called_with_cfg_loop(self):
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        self.assertGreater(self.benchmark.my_method.call_count, 0)

    def test__worker_process_called_without_cfg(self):
        scenario_cfg = {'runner': {}}
        aborted = multiprocessing.Event()
        aborted.set()
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', scenario_cfg, {},
            aborted, mock.Mock())

        self.benchmark_cls.assert_called_once_with(scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.teardown.assert_called_once()

    def test__worker_process_output_queue(self):
        self.benchmark.my_method = mock.Mock(return_value='my_result')
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        output_queue = mock.Mock()
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), output_queue)

        self._assert_defaults__worker_run_setup_and_teardown()
        output_queue.put.assert_has_calls(
            [mock.call('my_result', True, constants.QUEUE_PUT_TIMEOUT)])

    def test__worker_process_output_queue_multiple_iterations(self):
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        self.benchmark.my_method = self.MyMethod()
        output_queue = mock.Mock()
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), output_queue)

        self._assert_defaults__worker_run_setup_and_teardown()
        for idx in range(102, 101 + len(output_queue.method_calls)):
            output_queue.put.assert_has_calls(
                [mock.call(idx, True, constants.QUEUE_PUT_TIMEOUT)])

    def test__worker_process_queue(self):
        self.benchmark.my_method = self.MyMethod()
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        queue = mock.Mock()
        proxduration._worker_process(
            queue, self.benchmark_cls, 'my_method', self.scenario_cfg, {},
            multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        benchmark_output = {'timestamp': mock.ANY,
                            'sequence': 1,
                            'data': {'my_key': 102},
                            'errors': ''}
        queue.put.assert_has_calls(
            [mock.call(benchmark_output, True, constants.QUEUE_PUT_TIMEOUT)])

    def test__worker_process_queue_multiple_iterations(self):
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        self.benchmark.my_method = self.MyMethod()
        queue = mock.Mock()
        proxduration._worker_process(
            queue, self.benchmark_cls, 'my_method', self.scenario_cfg, {},
            multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        for idx in range(102, 101 + len(queue.method_calls)):
            benchmark_output = {'timestamp': mock.ANY,
                                'sequence': idx - 101,
                                'data': {'my_key': idx},
                                'errors': ''}
            queue.put.assert_has_calls(
                [mock.call(benchmark_output, True,
                           constants.QUEUE_PUT_TIMEOUT)])

    def test__worker_process_except_sla_validation_error_no_sla_cfg(self):
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()

    @mock.patch.object(proxduration.LOG, 'warning')
    def test__worker_process_except_sla_validation_error_sla_cfg_monitor(
            self, *args):
        self.scenario_cfg['sla'] = {'action': 'monitor'}
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method', self.scenario_cfg,
            {}, multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()

    def test__worker_process_raise_sla_validation_error_sla_cfg_default(self):
        self.scenario_cfg['sla'] = {}
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)
        with self.assertRaises(y_exc.SLAValidationError):
            proxduration._worker_process(
                mock.Mock(), self.benchmark_cls, 'my_method',
                self.scenario_cfg, {}, multiprocessing.Event(), mock.Mock())

        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.my_method.assert_called_once_with({})

    def test__worker_process_raise_sla_validation_error_sla_cfg_assert(self):
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        self.scenario_cfg['sla'] = {'action': 'assert'}
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.SLAValidationError)

        with self.assertRaises(y_exc.SLAValidationError):
            proxduration._worker_process(
                mock.Mock(), self.benchmark_cls, 'my_method',
                self.scenario_cfg, {}, multiprocessing.Event(), mock.Mock())

        self.benchmark_cls.assert_called_once_with(self.scenario_cfg, {})
        self.benchmark.setup.assert_called_once()
        self.benchmark.my_method.assert_called_once_with({})

    @mock.patch.object(proxduration.LOG, 'warning')
    def test__worker_process_queue_on_sla_validation_error_monitor(
            self, *args):
        self.scenario_cfg['sla'] = {'action': 'monitor'}
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.SLA_VALIDATION_ERROR_SIDE_EFFECT)
        queue = mock.Mock()
        proxduration._worker_process(
            queue, self.benchmark_cls, 'my_method', self.scenario_cfg, {},
            multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()
        benchmark_output = {'timestamp': mock.ANY,
                            'sequence': 1,
                            'data': {'my_key': 102},
                            'errors': ('My Case SLA validation failed. '
                                       'Error: my error message', )}
        queue.put.assert_has_calls(
            [mock.call(benchmark_output, True, constants.QUEUE_PUT_TIMEOUT)])

    @mock.patch.object(proxduration.LOG, 'exception')
    def test__worker_process_broad_exception(self, *args):
        self.benchmark.my_method = mock.Mock(
            side_effect=y_exc.YardstickException)
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        proxduration._worker_process(
            mock.Mock(), self.benchmark_cls, 'my_method',
            self.scenario_cfg, {}, multiprocessing.Event(), mock.Mock())

        self._assert_defaults__worker_run_setup_and_teardown()

    @mock.patch.object(proxduration.LOG, 'exception')
    def test__worker_process_queue_on_broad_exception(self, *args):
        self.benchmark.my_method = self.MyMethod(
            side_effect=self.MyMethod.BROAD_EXCEPTION_SIDE_EFFECT)
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}
        queue = mock.Mock()
        proxduration._worker_process(
            queue, self.benchmark_cls, 'my_method', self.scenario_cfg, {},
            multiprocessing.Event(), mock.Mock())

        benchmark_output = {'timestamp': mock.ANY,
                            'sequence': 1,
                            'data': {'my_key': 102},
                            'errors': mock.ANY}
        queue.put.assert_has_calls(
            [mock.call(benchmark_output, True, constants.QUEUE_PUT_TIMEOUT)])

    @mock.patch.object(proxduration.LOG, 'exception')
    def test__worker_process_benchmark_teardown_on_broad_exception(
            self, *args):
        self.benchmark.teardown = mock.Mock(
            side_effect=y_exc.YardstickException)
        self.scenario_cfg["runner"] = {"sampled": True, "duration": 0.1}

        with self.assertRaises(SystemExit) as raised:
            proxduration._worker_process(
                mock.Mock(), self.benchmark_cls, 'my_method',
                self.scenario_cfg, {}, multiprocessing.Event(), mock.Mock())
        self.assertEqual(1, raised.exception.code)
        self._assert_defaults__worker_run_setup_and_teardown()
