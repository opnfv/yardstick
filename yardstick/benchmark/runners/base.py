##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import importlib
import json
import logging
import multiprocessing
import subprocess
import time

log = logging.getLogger(__name__)

import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base as base_scenario


def _output_serializer_main(filename, queue):
    '''entrypoint for the singleton subprocess writing to outfile
    Use of this process enables multiple instances of a scenario without
    messing up the output file.
    '''
    with open(filename, 'a+') as outfile:
        while True:
            # blocks until data becomes available
            record = queue.get()
            if record == '_TERMINATE_':
                outfile.close()
                break
            else:
                json.dump(record, outfile)
                outfile.write('\n')


def _single_action(seconds, command, queue):
    '''entrypoint for the single action process'''
    log.debug("single action, fires after %d seconds (from now)", seconds)
    time.sleep(seconds)
    log.debug("single action: executing command: '%s'", command)
    data = subprocess.check_output(command, shell=True)
    log.debug("\n%s" % data)


def _periodic_action(interval, command, queue):
    '''entrypoint for the periodic action process'''
    log.debug("periodic action, fires every: %d seconds", interval)
    time_spent = 0
    while True:
        time.sleep(interval)
        time_spent += interval
        log.debug("periodic action, executing command: '%s'", command)
        data = subprocess.check_output(command, shell=True)
        log.debug("\n%s" % data)


class Runner(object):
    queue = None
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

        return Runner.get_cls(config["type"])(config, Runner.queue)

    @staticmethod
    def release(runner):
        '''Release the runner'''
        Runner.runners.remove(runner)
        # if this was the last runner, stop the output serializer subprocess
        if len(Runner.runners) == 0:
            log.debug("Stopping dump process")
            Runner.queue.put('_TERMINATE_')
            Runner.dump_process.join()

    @staticmethod
    def terminate_all():
        '''Terminate all runners (subprocesses)'''
        log.debug("Terminating all runners")
        for runner in Runner.runners:
            if runner.periodic_action_process:
                log.debug("Terminating periodic action process")
                runner.periodic_action_process.terminate()
                runner.periodic_action_process = None
            runner.process.terminate()
            runner.process.join()
            Runner.release(runner)

    def __init__(self, config, queue):
        self.context = {}
        self.config = config
        self.periodic_action_process = None
        self.result_queue = queue
        Runner.runners.append(self)

    def run_pre_start_action(self):
        '''run a potentially configured pre-start action'''
        if "pre-start-action" in self.config:
            command = self.config["pre-start-action"]["command"]
            log.debug("pre start action: command: '%s'" % command)
            data = subprocess.check_output(command, shell=True)
            log.debug("pre-start data: \n%s" % data)
            output = "{'pre-start-action-data': %s}" % data
            self.result_queue.put(output)

    def run_post_stop_action(self):
        '''run a potentially configured post-stop action'''
        if "post-stop-action" in self.config:
            command = self.config["post-stop-action"]["command"]
            log.debug("post stop action: command: '%s'" % command)
            data = subprocess.check_output(command, shell=True)
            log.debug("post-stop data: \n%s" % data)
            output = "{'post-stop-action-data': %s}" % data
            self.result_queue.put(output)

    def run(self, scenario_type, scenario_args):
        class_name = base_scenario.Scenario.get(scenario_type)
        path_split = class_name.split(".")
        module_path = ".".join(path_split[:-1])
        module = importlib.import_module(module_path)
        cls = getattr(module, path_split[-1])

        self.config['object'] = class_name

        self.run_pre_start_action()

        if "single-shot-action" in self.config:
            single_action_process = multiprocessing.Process(
                target=_single_action,
                name="single-shot-action",
                args=(self.config["single-shot-action"]["after"],
                      self.config["single-shot-action"]["command"],
                      self.result_queue))
            single_action_process.start()

        if "periodic-action" in self.config:
            self.periodic_action_process = multiprocessing.Process(
                target=_periodic_action,
                name="periodic-action",
                args=(self.config["periodic-action"]["interval"],
                      self.config["periodic-action"]["command"],
                      self.result_queue))
            self.periodic_action_process.start()

        self._run_benchmark(cls, "run", scenario_args)

    def join(self):
        self.process.join()
        if self.periodic_action_process:
            self.periodic_action_process.terminate()
            self.periodic_action_process = None
        self.run_post_stop_action()
        return self.process.exitcode
