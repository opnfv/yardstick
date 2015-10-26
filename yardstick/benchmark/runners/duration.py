##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

'''A runner that runs a specific time before it returns
'''

import os
import multiprocessing
import logging
import traceback
import time

from yardstick.benchmark.runners import base

LOG = logging.getLogger(__name__)


def _worker_process(queue, cls, method_name, scenario_cfg, context_cfg):

    sequence = 1

    runner_cfg = scenario_cfg['runner']

    interval = runner_cfg.get("interval", 1)
    duration = runner_cfg.get("duration", 60)
    LOG.info("worker START, duration %d sec, class %s", duration, cls)

    runner_cfg['runner_id'] = os.getpid()

    benchmark = cls(scenario_cfg, context_cfg)
    benchmark.setup()
    method = getattr(benchmark, method_name)

    sla_action = None
    if "sla" in scenario_cfg:
        sla_action = scenario_cfg["sla"].get("action", "assert")

    queue.put({'runner_id': runner_cfg['runner_id'],
               'scenario_cfg': scenario_cfg,
               'context_cfg': context_cfg})

    start = time.time()
    while True:

        LOG.debug("runner=%(runner)s seq=%(sequence)s START" %
                  {"runner": runner_cfg["runner_id"], "sequence": sequence})

        data = {}
        errors = ""

        try:
            method(data)
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

        record = {'runner_id': runner_cfg['runner_id'],
                  'benchmark': benchmark_output}

        queue.put(record)

        LOG.debug("runner=%(runner)s seq=%(sequence)s END" %
                  {"runner": runner_cfg["runner_id"], "sequence": sequence})

        sequence += 1

        if (errors and sla_action is None) or (time.time() - start > duration):
            LOG.info("worker END")
            break

    benchmark.teardown()


class DurationRunner(base.Runner):
    '''Run a scenario for a certain amount of time

If the scenario ends before the time has elapsed, it will be started again.

  Parameters
    duration - amount of time the scenario will be run for
        type:    int
        unit:    seconds
        default: 1 sec
    interval - time to wait between each scenario invocation
        type:    int
        unit:    seconds
        default: 1 sec
    '''
    __execution_type__ = 'Duration'

    def _run_benchmark(self, cls, method, scenario_cfg, context_cfg):
        self.process = multiprocessing.Process(
            target=_worker_process,
            args=(self.result_queue, cls, method, scenario_cfg, context_cfg))
        self.process.start()
