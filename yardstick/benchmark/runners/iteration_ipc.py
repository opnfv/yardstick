# Copyright 2018: Intel Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this is a modified copy of
# rally/rally/benchmark/runners/constant.py

"""A runner that runs a configurable number of times before it returns. Each
   iteration has a configurable timeout. The loop control depends on the
   feedback received from the running VNFs. The context PIDs from the VNFs
   to listen the messages from are given in the scenario "setup" method.
"""

import logging
import multiprocessing
import time
import traceback

import os

from yardstick.benchmark.runners import base
from yardstick.common import exceptions
from yardstick.common import messaging
from yardstick.common import utils
from yardstick.common.messaging import consumer
from yardstick.common.messaging import payloads


LOG = logging.getLogger(__name__)

QUEUE_PUT_TIMEOUT = 10
ITERATION_TIMEOUT = 180


class RunnerIterationIPCEndpoint(consumer.NotificationHandler):

    def started(self, ctxt, **kwargs):
        if ctxt['pid'] in self._ctx_pids:
            self._queue.put(
                {'pid': ctxt['pid'],
                 'action': messaging.TG_METHOD_STARTED,
                 'payload': payloads.TrafficGeneratorPayload.dict_to_obj(
                     kwargs)})

    def finished(self, ctxt, **kwargs):
        if ctxt['pid'] in self._ctx_pids:
            self._queue.put(
                {'pid': ctxt['pid'],
                 'action': messaging.TG_METHOD_FINISHED,
                 'payload': payloads.TrafficGeneratorPayload.dict_to_obj(
                     kwargs)})

    def iteration(self, ctxt, **kwargs):
        if ctxt['pid'] in self._ctx_pids:
            self._queue.put(
                {'pid': ctxt['pid'],
                 'action': messaging.TG_METHOD_ITERATION,
                 'payload': payloads.TrafficGeneratorPayload.dict_to_obj(
                     kwargs)})


class RunnerIterationIPCConsumer(consumer.MessagingConsumer):

    def __init__(self, _id, ctx_pids, queue):
        self._id = _id
        endpoints = [RunnerIterationIPCEndpoint(_id, ctx_pids, queue)]
        super(RunnerIterationIPCConsumer, self).__init__(
            messaging.TOPIC_TG, ctx_pids, endpoints)
        self._iterations = {ctx: [] for ctx in ctx_pids}
        self._queue = queue
        self.iteration_index = None

    def check_iteration_status(self, ):
        while not self._queue.empty():
            msg = self._queue.get(True, 1)
            if msg['action'] == messaging.TG_METHOD_ITERATION:
                pid_iter_list = self._iterations[msg['pid']]
                payload = msg['payload']
                pid_iter_list[payload.iteration - 1] = payload.data

        return all(len(pid_iter_list) == self.iteration_index
                   for pid_iter_list in self._iterations.values())

def _worker_process(queue, cls, method_name, scenario_cfg,
                    context_cfg, aborted, output_queue):
    sequence = 1
    runner_cfg = scenario_cfg['runner']
    mq_queue = multiprocessing.Queue()

    timeout = runner_cfg.get('timeout', ITERATION_TIMEOUT)
    iterations = runner_cfg.get('iterations', 1)
    run_step = runner_cfg.get('run_step', 'setup,run,teardown')
    ###delta = runner_cfg.get('delta', 2)
    LOG.info('Worker START. Iterations %d times, class %s', iterations, cls)

    runner_cfg['runner_id'] = os.getpid()

    benchmark = cls(scenario_cfg, context_cfg)
    method = getattr(benchmark, method_name)

    if 'setup' not in run_step:
        raise exceptions.RunnerIterationIPCSetupActionNeeded()
    producer_ctxs = benchmark.setup()
    if not producer_ctxs:
        raise exceptions.RunnerIterationIPCNoCtxs()

    mq_consumer = RunnerIterationIPCConsumer(os.getpid(),
                                             producer_ctxs,
                                             mq_queue)

    iteration_index = 1
    while 'run' in run_step:
        LOG.debug("runner=%(runner)s seq=%(sequence)s START",
                  {"runner": runner_cfg["runner_id"],
                   "sequence": iteration_index})
        data = {}
        errors = ''

        ##next_iteration = False
        mq_consumer.iteration_index = iteration_index
        utils.wait_until_true(
            mq_consumer.check_iteration_status, timeout=timeout, sleep=2)

        ########benchmark.pre_run_wait_time(timeout)

        try:
            result = method(data)

        except Exception:  # pylint: disable=broad-except
            errors = traceback.format_exc()
            LOG.exception(errors)
        else:
            if result:
                # add timeout for put so we don't block test
                # if we do timeout we don't care about dropping individual KPIs
                output_queue.put(result, True, QUEUE_PUT_TIMEOUT)

        # RAH: delete
        #####benchmark.post_run_wait_time(timeout)

        benchmark_output = {'timestamp': time.time(),
                            'sequence': sequence,
                            'data': data,
                            'errors': errors
                            }

        queue.put(benchmark_output, True, QUEUE_PUT_TIMEOUT)

        LOG.debug("runner=%(runner)s seq=%(sequence)s END",
                  {"runner": runner_cfg["runner_id"],
                   "sequence": iteration_index})

        iteration_index += 1
        if iteration_index > iterations:
            break

    if 'teardown' in run_step:
        try:
            benchmark.teardown()
        except Exception:
            LOG.exception('Exception during teardown process')
            raise SystemExit(1)

    LOG.debug('Queue size = %s', queue.qsize())
    LOG.debug('Output queue size = %s', output_queue.qsize())


class IterationIPCRunner(base.Runner):
    """Run a scenario for a configurable number of times.

    Each iteration has a configurable timeout. The loop control depends on the
    feedback received from the running VNFs. The context PIDs from the VNFs to
    listen the messages from are given in the scenario "setup" method.
    """
    __execution_type__ = 'IterationIPC'

    def _run_benchmark(self, cls, method, scenario_cfg, context_cfg):
        name = '{}-{}-{}'.format(
            self.__execution_type__, scenario_cfg.get('type'), os.getpid())
        self.process = multiprocessing.Process(
            name=name,
            target=_worker_process,
            args=(self.result_queue, cls, method, scenario_cfg,
                  context_cfg, self.aborted, self.output_queue))
        self.process.start()
