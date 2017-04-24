# Copyright 2014: Mirantis Inc.
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

"""A runner that runs a specific time before it returns
"""

from __future__ import absolute_import
import os
import multiprocessing
import logging
import traceback
import time

from collections import Mapping
from contextlib import contextmanager
from itertools import takewhile
from six.moves import zip

from yardstick.benchmark.runners import base

LOG = logging.getLogger(__name__)


class SearchRunnerHelper(object):

    def __init__(self, cls, method_name, scenario_cfg, context_cfg, aborted):
        super(SearchRunnerHelper, self).__init__()
        self.cls = cls
        self.method_name = method_name
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.aborted = aborted
        self.runner_cfg = scenario_cfg['runner']
        self.run_step = self.runner_cfg.get("run_step", "setup,run,teardown")
        self.timeout = self.runner_cfg.get("timeout", 60)
        self.interval = self.runner_cfg.get("interval", 1)
        self.benchmark = None
        self.method = None

    def __call__(self, *args, **kwargs):
        if self.method is None:
            raise RuntimeError
        return self.method(*args, **kwargs)

    @contextmanager
    def get_benchmark_instance(self):
        self.benchmark = self.cls(self.scenario_cfg, self.context_cfg)

        if 'setup' in self.run_step:
            self.benchmark.setup()

        self.method = getattr(self.benchmark, self.method_name)
        LOG.info("worker START, timeout %d sec, class %s", self.timeout, self.cls)
        try:
            yield self
        finally:
            if 'teardown' in self.run_step:
                self.benchmark.teardown()

    def is_not_done(self):
        if 'run' not in self.run_step:
            raise StopIteration

        max_time = time.time() + self.timeout

        abort_iter = iter(self.aborted.is_set, True)
        time_iter = takewhile(lambda t_now: t_now <= max_time, iter(time.time, -1))

        for seq, _ in enumerate(zip(abort_iter, time_iter), 1):
            yield seq
            time.sleep(self.interval)


class SearchRunner(base.Runner):
    """Run a scenario for a certain amount of time

If the scenario ends before the time has elapsed, it will be started again.

  Parameters
    timeout - amount of time the scenario will be run for
        type:    int
        unit:    seconds
        default: 1 sec
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    """
    __execution_type__ = 'Search'

    def __init__(self, config):
        super(SearchRunner, self).__init__(config)
        self.runner_cfg = None
        self.runner_id = None
        self.sla_action = None
        self.worker_helper = None

    def _worker_run_once(self, sequence):
        LOG.debug("runner=%s seq=%s START", self.runner_id, sequence)

        data = {}
        errors = ""

        try:
            self.worker_helper(data)
        except AssertionError as assertion:
            # SLA validation failed in scenario, determine what to do now
            if self.sla_action == "assert":
                raise
            elif self.sla_action == "monitor":
                LOG.warning("SLA validation failed: %s", assertion.args)
                errors = assertion.args
        except Exception as e:
            errors = traceback.format_exc()
            LOG.exception(e)

        record = {
            'runner_id': self.runner_id,
            'benchmark': {
                'timestamp': time.time(),
                'sequence': sequence,
                'data': data,
                'errors': errors,
            },
        }

        self.result_queue.put(record)

        LOG.debug("runner=%s seq=%s END", self.runner_id, sequence)

        # Have to search through all the VNF KPIs
        kpi_done = any(kpi.get('done') for kpi in data.values() if isinstance(kpi, Mapping))

        return kpi_done or (errors and self.sla_action is None)

    def _worker_run(self, cls, method_name, scenario_cfg, context_cfg):
        self.runner_cfg = scenario_cfg['runner']
        self.runner_id = self.runner_cfg['runner_id'] = os.getpid()

        self.worker_helper = SearchRunnerHelper(cls, method_name, scenario_cfg,
                                                context_cfg, self.aborted)

        try:
            self.sla_action = scenario_cfg['sla'].get('action', 'assert')
        except KeyError:
            self.sla_action = None

        self.result_queue.put({
            'runner_id': self.runner_id,
            'scenario_cfg': scenario_cfg,
            'context_cfg': context_cfg
        })

        with self.worker_helper.get_benchmark_instance():
            for sequence in self.worker_helper.is_not_done():
                if self._worker_run_once(sequence):
                    LOG.info("worker END")
                    break

    def _run_benchmark(self, cls, method, scenario_cfg, context_cfg):
        self.process = multiprocessing.Process(
            target=self._worker_run,
            args=(cls, method, scenario_cfg, context_cfg))
        self.process.start()
