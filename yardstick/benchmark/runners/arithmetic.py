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

"""A runner that every run arithmetically steps specified input value(s) to
the scenario. This just means step value(s) is added to the previous value(s).
It is possible to combine several named input values and run with those either
as nested for loops or combine each i:th index of each "input value list"
until the end of the shortest list is reached (optimally all lists should be
defined with the same number of values when using such iter_type).
"""

from __future__ import absolute_import

import itertools
import logging
import multiprocessing
import os
import time
import traceback

import six
from six.moves import range

from yardstick.benchmark.runners import base

LOG = logging.getLogger(__name__)


def _worker_process(queue, cls, method_name, scenario_cfg,
                    context_cfg, aborted, output_queue):

    sequence = 1

    runner_cfg = scenario_cfg['runner']

    interval = runner_cfg.get("interval", 1)
    if 'options' in scenario_cfg:
        options = scenario_cfg['options']
    else:  # options must be instatiated if not present in yaml
        options = {}
        scenario_cfg['options'] = options

    runner_cfg['runner_id'] = os.getpid()

    LOG.info("worker START, class %s", cls)

    benchmark = cls(scenario_cfg, context_cfg)
    benchmark.setup()
    method = getattr(benchmark, method_name)

    sla_action = None
    if "sla" in scenario_cfg:
        sla_action = scenario_cfg["sla"].get("action", "assert")

    # To both be able to include the stop value and handle backwards stepping
    def margin(start, stop):
        return -1 if start > stop else 1

    param_iters = \
        [range(d['start'], d['stop'] + margin(d['start'], d['stop']),
               d['step']) for d in runner_cfg['iterators']]
    param_names = [d['name'] for d in runner_cfg['iterators']]

    iter_type = runner_cfg.get("iter_type", "nested_for_loops")

    if iter_type == 'nested_for_loops':
        # Create a complete combination set of all parameter lists
        loop_iter = itertools.product(*param_iters)
    elif iter_type == 'tuple_loops':
        # Combine each i;th index of respective parameter list
        loop_iter = six.moves.zip(*param_iters)
    else:
        LOG.warning("iter_type unrecognized: %s", iter_type)
        raise TypeError("iter_type unrecognized: %s", iter_type)

    # Populate options and run the requested method for each value combination
    for comb_values in loop_iter:

        if aborted.is_set():
            break

        LOG.debug("runner=%(runner)s seq=%(sequence)s START",
                  {"runner": runner_cfg["runner_id"], "sequence": sequence})

        for i, value in enumerate(comb_values):
            options[param_names[i]] = value

        data = {}
        errors = ""

        try:
            result = method(data)
        except AssertionError as assertion:
            # SLA validation failed in scenario, determine what to do now
            if sla_action == "assert":
                raise
            elif sla_action == "monitor":
                LOG.warning("SLA validation failed: %s", assertion.args)
                errors = assertion.args
        except Exception as e:
            errors = traceback.format_exc()
            LOG.exception(e)
        else:
            if result:
                output_queue.put(result)

        time.sleep(interval)

        benchmark_output = {
            'timestamp': time.time(),
            'sequence': sequence,
            'data': data,
            'errors': errors
        }

        queue.put(benchmark_output)

        LOG.debug("runner=%(runner)s seq=%(sequence)s END",
                  {"runner": runner_cfg["runner_id"], "sequence": sequence})

        sequence += 1

        if errors and sla_action is None:
            break

    benchmark.teardown()
    LOG.info("worker END")


class ArithmeticRunner(base.Runner):
    """Run a scenario arithmetically stepping input value(s)

  Parameters
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    iter_type: - Iteration type of input parameter(s): nested_for_loops
                 or tuple_loops
        type:    string
        unit:    na
        default: nested_for_loops
    -
      name - name of scenario option that will be increased for each invocation
          type:    string
          unit:    na
          default: na
      start - value to use in first invocation of scenario
          type:    int
          unit:    na
          default: none
      stop - value indicating end of invocation. Can be set to same
             value as start for one single value.
          type:    int
          unit:    na
          default: none
      step - value added to start value in next invocation of scenario.
             Must not be set to zero. Can be set negative if start > stop
          type:    int
          unit:    na
          default: none
    -
      name - and so on......
    """

    __execution_type__ = 'Arithmetic'

    def _run_benchmark(self, cls, method, scenario_cfg, context_cfg):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, scenario_cfg,
                  context_cfg, self.aborted, self.output_queue))
        self.process.start()
