##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import importlib
import logging

log = logging.getLogger(__name__)

import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base as base_scenario


class Runner(object):
    dump_process = None
    runners = []

    @staticmethod
    def get_cls(runner_type):
        '''return class of specified type'''
        for runner in utils.itersubclasses(Runner):
            if runner_type == runner.__execution_type__:
                return runner
        raise RuntimeError("No such runner_type %s" % runner_type)

    @staticmethod
    def get_types():
        '''return a list of known runner type (class) names'''
        types = []
        for runner in utils.itersubclasses(Runner):
            types.append(runner)
        return types

    @staticmethod
    def get(config):
        '''Returns instance of a scenario runner for execution type.
        '''
        return Runner._get_cls(config["type"])(config)

    @staticmethod
    def release(runner):
        '''Release the runner'''
        Runner.runners.remove(runner)

    @staticmethod
    def terminate_all():
        '''Terminate all runners (subprocesses)'''
        log.debug("Terminating all runners")
        for runner in Runner.runners:
            runner.process.terminate()
            runner.process.join()
            Runner.release(runner)

    def __init__(self, config):
        self.context = {}
        self.config = config
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
