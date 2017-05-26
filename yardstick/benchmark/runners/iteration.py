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

"""A runner that runs a configurable number of times before it returns
"""

from __future__ import absolute_import
import os
import multiprocessing
import logging
import traceback
import time

from yardstick.benchmark.runners import base

LOG = logging.getLogger(__name__)


def _worker_process(queue, cls, method_name, scenario_cfg,
                    context_cfg, aborted):

    sequence = 1

    runner_cfg = scenario_cfg['runner']

    interval = runner_cfg.get("interval", 1)
    iterations = runner_cfg.get("iterations", 1)
    run_step = runner_cfg.get("run_step", "setup,run,teardown")

    delta = runner_cfg.get("delta", 2)
    LOG.info("worker START, iterations %d times, class %s", iterations, cls)

    runner_cfg['runner_id'] = os.getpid()

    benchmark = cls(scenario_cfg, context_cfg)
    if "setup" in run_step:
        benchmark.setup()

    method = getattr(benchmark, method_name)

    queue.put({'runner_id': runner_cfg['runner_id'],
               'scenario_cfg': scenario_cfg,
               'context_cfg': context_cfg})

    sla_action = None
    if "sla" in scenario_cfg:
        sla_action = scenario_cfg["sla"].get("action", "assert")
    if "run" in run_step:
        while True:

            LOG.debug("runner=%(runner)s seq=%(sequence)s START",
                      {"runner": runner_cfg["runner_id"],
                       "sequence": sequence})

            data = {}
            errors = ""

            try:
                method(data)
            except AssertionError as assertion:
                # SLA validation failed in scenario, determine what to do now
                if sla_action == "assert":
                    raise
                elif sla_action == "monitor":
                    LOG.warning("SLA validation failed: %s", assertion.args)
                    errors = assertion.args
                elif sla_action == "rate-control":
                    try:
                        scenario_cfg['options']['rate']
                    except KeyError:
                        scenario_cfg.setdefault('options', {})
                        scenario_cfg['options']['rate'] = 100

                    scenario_cfg['options']['rate'] -= delta
                    sequence = 1
                    continue
            except Exception as e:
                errors = traceback.format_exc()
                LOG.exception(e)

            time.sleep(interval)

            benchmark_output = {
                'timestamp': time.time(),
                'sequence': sequence,
                'data': data,
                'errors': errors
            }

            record = {'runner_id': runner_cfg['runner_id'],
                      'benchmark': benchmark_output}

            queue.put(record)

            LOG.debug("runner=%(runner)s seq=%(sequence)s END",
                      {"runner": runner_cfg["runner_id"],
                       "sequence": sequence})

            sequence += 1

            if (errors and sla_action is None) or \
                    (sequence > iterations or aborted.is_set()):
                LOG.info("worker END")
                break
    if "teardown" in run_step:
        benchmark.teardown()


class IterationRunner(base.Runner):
    """Run a scenario for a configurable number of times

If the scenario ends before the time has elapsed, it will be started again.

  Parameters
    iterations - amount of times the scenario will be run for
        type:    int
        unit:    na
        default: 1
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    """
    __execution_type__ = 'Iteration'

    def _run_benchmark(self, cls, method, scenario_cfg, context_cfg):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, scenario_cfg,
                  context_cfg, self.aborted))
        self.process.start()
