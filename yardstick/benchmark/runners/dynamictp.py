# Copyright 2016: Nokia
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

"""A runner that searches for the max throughput with binary search
"""

import os
import multiprocessing
import logging
import traceback
import time

from yardstick.benchmark.runners import base

LOG = logging.getLogger(__name__)


def _worker_process(queue, cls, method_name, scenario_cfg,
                    context_cfg, aborted):  # pragma: no cover

    runner_cfg = scenario_cfg['runner']
    iterations = runner_cfg.get("iterations", 1)
    interval = runner_cfg.get("interval", 1)
    run_step = runner_cfg.get("run_step", "setup,run,teardown")
    delta = runner_cfg.get("delta", 1000)
    options_cfg = scenario_cfg['options']
    initial_rate = options_cfg.get("pps", 1000000)
    LOG.info("worker START, class %s", cls)

    runner_cfg['runner_id'] = os.getpid()

    benchmark = cls(scenario_cfg, context_cfg)
    if "setup" in run_step:
        benchmark.setup()

    method = getattr(benchmark, method_name)

    queue.put({'runner_id': runner_cfg['runner_id'],
               'scenario_cfg': scenario_cfg,
               'context_cfg': context_cfg})

    if "run" in run_step:
        iterator = 0
        search_max = initial_rate
        search_min = 0
        while iterator < iterations:
            search_min = int(search_min / 2)
            scenario_cfg['options']['pps'] = search_max
            search_max_found = False
            max_throuput_found = False
            sequence = 0

            last_min_data = {}
            last_min_data['packets_per_second'] = 0

            while True:
                sequence += 1

                data = {}
                errors = ""
                too_high = False

                LOG.debug("sequence: %s search_min: %s search_max: %s",
                          sequence, search_min, search_max)

                try:
                    method(data)
                except AssertionError as assertion:
                    LOG.warning("SLA validation failed: %s" % assertion.args)
                    too_high = True
                except Exception as e:
                    errors = traceback.format_exc()
                    LOG.exception(e)

                actual_pps = data['packets_per_second']

                if too_high:
                    search_max = actual_pps

                    if not search_max_found:
                        search_max_found = True
                else:
                    last_min_data = data
                    search_min = actual_pps

                    # Check if the actual rate is well below the asked rate
                    if scenario_cfg['options']['pps'] > actual_pps * 1.5:
                        search_max = actual_pps
                        LOG.debug("Sender reached max tput: %s", search_max)
                    elif not search_max_found:
                        search_max = int(actual_pps * 1.5)

                if ((search_max - search_min) < delta) or \
                   (search_max <= search_min) or (10 <= sequence):
                    if last_min_data['packets_per_second'] > 0:
                        data = last_min_data

                    benchmark_output = {
                        'timestamp': time.time(),
                        'sequence': sequence,
                        'data': data,
                        'errors': errors
                    }

                    record = {
                        'runner_id': runner_cfg['runner_id'],
                        'benchmark': benchmark_output
                    }

                    queue.put(record)
                    max_throuput_found = True

                if (errors) or aborted.is_set() or max_throuput_found:
                    LOG.info("worker END")
                    break

                if not search_max_found:
                    scenario_cfg['options']['pps'] = search_max
                else:
                    scenario_cfg['options']['pps'] = \
                        (search_max - search_min) / 2 + search_min

                time.sleep(interval)

            iterator += 1
            LOG.debug("iterator: %s iterations: %s", iterator, iterations)

    if "teardown" in run_step:
        benchmark.teardown()


class IterationRunner(base.Runner):
    '''Run a scenario to find the max throughput

If the scenario ends before the time has elapsed, it will be started again.

  Parameters
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    delta - stop condition for the search.
        type:	 int
        unit:	 pps
        default: 1000 pps
    '''
    __execution_type__ = 'Dynamictp'

    def _run_benchmark(self, cls, method, scenario_cfg, context_cfg):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, scenario_cfg,
                  context_cfg, self.aborted))
        self.process.start()
