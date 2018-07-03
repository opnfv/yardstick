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

from yardstick.benchmark.runners import base as base_runner
from yardstick.common import exceptions
from yardstick.common import messaging
from yardstick.common import utils
from yardstick.common.messaging import consumer
from yardstick.common.messaging import payloads


LOG = logging.getLogger(__name__)

QUEUE_PUT_TIMEOUT = 10
ITERATION_TIMEOUT = 180


class RunnerIterationIPCEndpoint(consumer.NotificationHandler):
    """Endpoint class for ``RunnerIterationIPCConsumer``"""

    def tg_method_started(self, ctxt, **kwargs):
        if ctxt['id'] in self._ctx_ids:
            self._queue.put(
                {'id': ctxt['id'],
                 'action': messaging.TG_METHOD_STARTED,
                 'payload': payloads.TrafficGeneratorPayload.dict_to_obj(
                     kwargs)},
                QUEUE_PUT_TIMEOUT)

    def tg_method_finished(self, ctxt, **kwargs):
        if ctxt['id'] in self._ctx_ids:
            self._queue.put(
                {'id': ctxt['id'],
                 'action': messaging.TG_METHOD_FINISHED,
                 'payload': payloads.TrafficGeneratorPayload.dict_to_obj(
                     kwargs)})

    def tg_method_iteration(self, ctxt, **kwargs):
        if ctxt['id'] in self._ctx_ids:
            self._queue.put(
                {'id': ctxt['id'],
                 'action': messaging.TG_METHOD_ITERATION,
                 'payload': payloads.TrafficGeneratorPayload.dict_to_obj(
                     kwargs)})


class RunnerIterationIPCConsumer(consumer.MessagingConsumer):
    """MQ consumer for "IterationIPC" runner"""

    def __init__(self, _id, ctx_ids):
        self._id = _id
        self._queue = multiprocessing.Queue()
        endpoints = [RunnerIterationIPCEndpoint(_id, ctx_ids, self._queue)]
        super(RunnerIterationIPCConsumer, self).__init__(
            messaging.TOPIC_TG, ctx_ids, endpoints)
        self._kpi_per_id = {ctx: [] for ctx in ctx_ids}
        self.iteration_index = None

    def is_all_kpis_received_in_iteration(self):
        """Check if all producers registered have sent the ITERATION msg

        During the present iteration, all producers (traffic generators) must
        start and finish the traffic injection, and at the end of the traffic
        injection a TG_METHOD_ITERATION must be sent. This function will check
        all KPIs in the present iteration are received. E.g.:
          self.iteration_index = 2

          self._kpi_per_id = {
            'ctx1': [kpi0, kpi1, kpi2],
            'ctx2': [kpi0, kpi1]}          --> return False

          self._kpi_per_id = {
            'ctx1': [kpi0, kpi1, kpi2],
            'ctx2': [kpi0, kpi1, kpi2]}    --> return True
        """
        while not self._queue.empty():
            msg = self._queue.get(True, 1)
            if msg['action'] == messaging.TG_METHOD_ITERATION:
                id_iter_list = self._kpi_per_id[msg['id']]
                id_iter_list.append(msg['payload'].kpi)

        return all(len(id_iter_list) == self.iteration_index
                   for id_iter_list in self._kpi_per_id.values())


def _worker_process(queue, cls, method_name, scenario_cfg,
                    context_cfg, aborted, output_queue):  # pragma: no cover
    runner_cfg = scenario_cfg['runner']

    timeout = runner_cfg.get('timeout', ITERATION_TIMEOUT)
    iterations = runner_cfg.get('iterations', 1)
    run_step = runner_cfg.get('run_step', 'setup,run,teardown')
    LOG.info('Worker START. Iterations %d times, class %s', iterations, cls)

    runner_cfg['runner_id'] = os.getpid()

    benchmark = cls(scenario_cfg, context_cfg)
    method = getattr(benchmark, method_name)

    if 'setup' not in run_step:
        raise exceptions.RunnerIterationIPCSetupActionNeeded()
    benchmark.setup()
    producer_ctxs = benchmark.get_mq_ids()
    if not producer_ctxs:
        raise exceptions.RunnerIterationIPCNoCtxs()

    mq_consumer = RunnerIterationIPCConsumer(os.getpid(), producer_ctxs)
    mq_consumer.start_rpc_server()
    mq_producer = base_runner.RunnerProducer(scenario_cfg['task_id'])

    iteration_index = 1
    while 'run' in run_step:
        LOG.debug('runner=%(runner)s seq=%(sequence)s START',
                  {'runner': runner_cfg['runner_id'],
                   'sequence': iteration_index})
        data = {}
        result = None
        errors = ''
        mq_consumer.iteration_index = iteration_index

        try:
            utils.wait_until_true(
                mq_consumer.is_all_kpis_received_in_iteration,
                timeout=timeout, sleep=2)
            result = method(data)
        except Exception:  # pylint: disable=broad-except
            errors = traceback.format_exc()
            LOG.exception(errors)

        if result:
            output_queue.put(result, True, QUEUE_PUT_TIMEOUT)
        benchmark_output = {'timestamp': time.time(),
                            'sequence': iteration_index,
                            'data': data,
                            'errors': errors}
        queue.put(benchmark_output, True, QUEUE_PUT_TIMEOUT)

        LOG.debug('runner=%(runner)s seq=%(sequence)s END',
                  {'runner': runner_cfg['runner_id'],
                   'sequence': iteration_index})

        iteration_index += 1
        if iteration_index > iterations or aborted.is_set():
            LOG.info('"IterationIPC" worker END')
            break

    if 'teardown' in run_step:
        try:
            benchmark.teardown()
        except Exception:
            LOG.exception('Exception during teardown process')
            mq_consumer.stop_rpc_server()
            raise SystemExit(1)

    LOG.debug('Data queue size = %s', queue.qsize())
    LOG.debug('Output queue size = %s', output_queue.qsize())
    mq_consumer.stop_rpc_server()


class IterationIPCRunner(base_runner.Runner):
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
