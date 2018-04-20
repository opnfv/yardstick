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

import multiprocessing
import time
import os
import uuid

import mock

from yardstick.benchmark.runners import iteration_ipc
from yardstick.common import messaging
from yardstick.common.messaging import payloads
from yardstick.tests.unit import base as ut_base


class RunnerIterationIPCEndpointTestCase(ut_base.BaseUnitTestCase):

    def setUp(self):
        self._id = uuid.uuid1().int
        self._ctx_pids = [uuid.uuid1().int, uuid.uuid1().int]
        self._queue = multiprocessing.Queue()
        self.runner = iteration_ipc.RunnerIterationIPCEndpoint(
            self._id, self._ctx_pids, self._queue)
        self._kwargs = {'version': 1, 'iteration': 10, 'kpi': {}}
        self._pload_dict = payloads.TrafficGeneratorPayload.dict_to_obj(
            self._kwargs).obj_to_dict()

    def test_tg_method_started(self):
        self._queue.empty()
        ctxt = {'pid': self._ctx_pids[0]}
        self.runner.tg_method_started(ctxt, **self._kwargs)
        time.sleep(0.2)

        output = []
        while not self._queue.empty():
            output.append(self._queue.get(True, 1))

        self.assertEqual(1, len(output))
        self.assertEqual(self._ctx_pids[0], output[0]['pid'])
        self.assertEqual(messaging.TG_METHOD_STARTED, output[0]['action'])
        self.assertEqual(self._pload_dict, output[0]['payload'].obj_to_dict())

    def test_tg_method_finished(self):
        self._queue.empty()
        ctxt = {'pid': self._ctx_pids[0]}
        self.runner.tg_method_finished(ctxt, **self._kwargs)
        time.sleep(0.2)

        output = []
        while not self._queue.empty():
            output.append(self._queue.get(True, 1))

        self.assertEqual(1, len(output))
        self.assertEqual(self._ctx_pids[0], output[0]['pid'])
        self.assertEqual(messaging.TG_METHOD_FINISHED, output[0]['action'])
        self.assertEqual(self._pload_dict, output[0]['payload'].obj_to_dict())

    def test_tg_method_iteration(self):
        self._queue.empty()
        ctxt = {'pid': self._ctx_pids[0]}
        self.runner.tg_method_iteration(ctxt, **self._kwargs)
        time.sleep(0.2)

        output = []
        while not self._queue.empty():
            output.append(self._queue.get(True, 1))

        self.assertEqual(1, len(output))
        self.assertEqual(self._ctx_pids[0], output[0]['pid'])
        self.assertEqual(messaging.TG_METHOD_ITERATION, output[0]['action'])
        self.assertEqual(self._pload_dict, output[0]['payload'].obj_to_dict())


class RunnerIterationIPCConsumerTestCase(ut_base.BaseUnitTestCase):

    def setUp(self):
        self._id = uuid.uuid1().int
        self._ctx_pids = [uuid.uuid1().int, uuid.uuid1().int]
        self._queue = mock.Mock()
        self.consumer = iteration_ipc.RunnerIterationIPCConsumer(
            self._id, self._ctx_pids, self._queue)

    def test__init(self):
        self.assertEqual({self._ctx_pids[0]: [], self._ctx_pids[1]: []},
                         self.consumer._kpi_per_pid)

    def test_check_iteration_status_action_iteration(self):
        payload = payloads.TrafficGeneratorPayload(
            version=1, iteration=1, kpi={})
        msg1 = {'action': messaging.TG_METHOD_ITERATION,
                'pid': self._ctx_pids[0], 'payload': payload}
        msg2 = {'action': messaging.TG_METHOD_ITERATION,
                'pid': self._ctx_pids[1], 'payload': payload}
        self.consumer.iteration_index = 1

        self._queue.empty.side_effect = [False, True]
        self._queue.get.return_value = msg1
        self.assertFalse(self.consumer.check_iteration_status())

        self._queue.empty.side_effect = [False, True]
        self._queue.get.return_value = msg2
        self.assertTrue(self.consumer.check_iteration_status())


class IterationIPCRunnerTestCase(ut_base.BaseUnitTestCase):

    @mock.patch.object(iteration_ipc, '_worker_process')
    @mock.patch.object(os, 'getpid', return_value=12345678)
    @mock.patch.object(multiprocessing, 'Process', return_value=mock.Mock())
    def test__run_benchmark(self, mock_process, mock_getpid, mock_worker):
        method = 'method'
        scenario_cfg = {'type': 'scenario_type'}
        context_cfg = 'context_cfg'
        name = '%s-%s-%s' % ('IterationIPC', 'scenario_type', 12345678)
        runner = iteration_ipc.IterationIPCRunner(mock.ANY)
        mock_getpid.reset_mock()

        runner._run_benchmark('class', method, scenario_cfg, context_cfg)
        mock_process.assert_called_once_with(
            name=name,
            target=mock_worker,
            args=(runner.result_queue, 'class', method, scenario_cfg,
                  context_cfg, runner.aborted, runner.output_queue))
        mock_getpid.assert_called_once()
