##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

'''A runner that every run changes a specified input value to the scenario.
The step value to change is specified in a list in the input file.
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
    arg_name = context.get('scenario_option_name')
    steps = context.get('steps')
    options = scenario_args['options']
    start = options.get(arg_name, 0)

    # if the inital step is not first in the steps list
    if start != steps[0]:
        steps.insert(0, start)

    context['runner'] = os.getpid()

    LOG.info("worker START, steps(%s, %s), class %s",
             arg_name, steps, cls)

    benchmark = cls(context)
    benchmark.setup()
    method = getattr(benchmark, method_name)

    record_context = {"runner": context["runner"],
                      "host": context["host"]}

    sla_action = None
    if "sla" in scenario_args:
        sla_action = scenario_args["sla"].get("action", "assert")

    for value in steps:
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


class StepperRunner(base.Runner):
    '''Run a scenario by changing an input value defined in a list

  Parameters
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    name - name of scenario option that will be increased for each invocation
        type:    string
        unit:    na
        default: none
    steps - list of values which are executed in their respective scenarios
        type:    [int]
        unit:    na
        default: none
    '''

    __execution_type__ = 'Stepper'

    def _run_benchmark(self, cls, method, scenario_args):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, self.config, scenario_args))
        self.process.start()
