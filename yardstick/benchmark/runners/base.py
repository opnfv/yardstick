##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import importlib
import multiprocessing
import json
import logging

log = logging.getLogger(__name__)

import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base as base_scenario


def _output_serializer_main(filename, queue):
    '''entrypoint for the singleton subprocess writing to outfile
    Use of this process enables multiple instances of a scenario without
    messing up the output file.
    '''
    with open(filename, 'w') as outfile:
        while True:
            # blocks until data becomes available
            record = queue.get()
            if record == '_TERMINATE_':
                outfile.close()
                break
            else:
                json.dump(record, outfile)
                outfile.write('\n')


class Runner(object):
    queue = None
    dump_process = None
    runners = []

    @staticmethod
    def _get_cls(runner_type):
        for runner in utils.itersubclasses(Runner):
            if runner_type == runner.__execution_type__:
                return runner
        raise RuntimeError("No such runner_type %s" % runner_type)

    @staticmethod
    def get(config):
        """Returns instance of a scenario runner for execution type.
        """
        # if there is no runner, start the output serializer subprocess
        if len(Runner.runners) == 0:
            log.debug("Starting dump process file '%s'" %
                      config["output_filename"])
            Runner.queue = multiprocessing.Queue()
            Runner.dump_process = multiprocessing.Process(
                target=_output_serializer_main,
                name="Dumper",
                args=(config["output_filename"], Runner.queue))
            Runner.dump_process.start()

        return Runner._get_cls(config["type"])(config, Runner.queue)

    @staticmethod
    def release(runner):
        '''Release the runner'''
        Runner.runners.remove(runner)
        # if this was the last runner, stop the output serializer subprocess
        if len(Runner.runners) == 0:
            log.debug("Stopping dump process")
            Runner.queue.put('_TERMINATE_')
            Runner.dump_process.join()

    def __init__(self, config, queue):
        self.context = {}
        self.config = config
        self.result_queue = queue
        Runner.runners.append(self)

    def run(self, scenario_type, scenario_args):
        class_name = base_scenario.Scenario.get(scenario_type)
        path_split = class_name.split(".")
        module_path = ".".join(path_split[:-1])
        module = importlib.import_module(module_path)
        cls = getattr(module, path_split[-1])

        self.config['object'] = class_name
        self._run_benchmark(cls, "run", scenario_args)

    def join(self):
        self.process.join()
        return self.process.exitcode
