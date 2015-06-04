##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

'''A runner that every run arithmetically steps a specified input value to
the scenario. This just means a step value is added to the previous value.
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
    arg_name = context.get('name')
    stop = context.get('stop')
    step = context.get('step')
    options = scenario_args['options']
    start = options.get(arg_name, 0)

    context['runner'] = os.getpid()

    LOG.info("worker START, step(%s, %d, %d, %d), class %s",
             arg_name, start, stop, step, cls)

    benchmark = cls(context)
    benchmark.setup()
    method = getattr(benchmark, method_name)

    record_context = {"runner": context["runner"],
                      "host": context["host"]}

    sla_action = None
    if "sla" in scenario_args:
        sla_action = scenario_args["sla"].get("action", "assert")

    for value in range(start, stop+step, step):

        options[arg_name] = value

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

        queue.put({'context': record_context, 'sargs:': scenario_args,
                   'benchmark': benchmark_output})

        LOG.debug("runner=%(runner)s seq=%(sequence)s END" %
                  {"runner": context["runner"], "sequence": sequence})

        sequence += 1

        if errors:
            break

    benchmark.teardown()
    LOG.info("worker END")


class ArithmeticRunner(base.Runner):

    __execution_type__ = 'Arithmetic'

    def _run_benchmark(self, cls, method, scenario_args):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, self.config, scenario_args))
        self.process.start()
