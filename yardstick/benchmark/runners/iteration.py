##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

'''A runner that runs a configurable number of times before it returns
'''

import os
import multiprocessing
import logging
import traceback
import time

from yardstick.benchmark.runners import base

LOG = logging.getLogger(__name__)


def _worker_process(queue, cls, method_name, context, scenario_args):

    sequence = 1

    interval = context.get("interval", 1)
    iteration = context.get("iteration", 60)
    LOG.info("worker START, iteration %d sec, class %s", iteration, cls)

    context['runner'] = os.getpid()

    benchmark = cls(context)
    benchmark.setup()
    method = getattr(benchmark, method_name)

    record_context = {"runner": context["runner"],
                      "host": context["host"]}

    sla_action = None
    if "sla" in scenario_args:
        sla_action = scenario_args["sla"].get("action", "assert")

    while True:

        LOG.debug("runner=%(runner)s seq=%(sequence)s START" %
                  {"runner": context["runner"], "sequence": sequence})

        data = {}
        errors = ""

        try:
            data = method(scenario_args)
        except AssertionError as assertion:
            # SLA validation failed in scenario, determine what to do now
            if sla_action == "assert":
                raise
            elif sla_action == "monitor":
                LOG.warning("SLA validation failed: %s" % assertion.args)
                errors = assertion.args
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

        queue.put({'context': record_context, 'sargs': scenario_args,
                   'benchmark': benchmark_output})

        LOG.debug("runner=%(runner)s seq=%(sequence)s END" %
                  {"runner": context["runner"], "sequence": sequence})

        sequence += 1

        if (errors and sla_action is None) or (sequence > iteration):
            LOG.info("worker END")
            break

    benchmark.teardown()


class IterationRunner(base.Runner):
    '''Run a scenario for a configurable number of times

If the scenario ends before the time has elapsed, it will be started again.

  Parameters
    iteration - amount of times the scenario will be run for
        type:    int
        unit:    times
        default: 60 times
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    '''
    __execution_type__ = 'Iteration'

    def _run_benchmark(self, cls, method, scenario_args):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, self.config, scenario_args))
        self.process.start()
