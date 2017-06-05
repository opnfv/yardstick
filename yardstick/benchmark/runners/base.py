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
# rally/rally/benchmark/runners/base.py

from __future__ import absolute_import
import importlib
import logging
import multiprocessing
import subprocess
import time
import os
import traceback

from oslo_config import cfg

import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base as base_scenario
from yardstick.dispatcher.base import Base as DispatcherBase

log = logging.getLogger(__name__)

CONF = cfg.CONF


def _output_serializer_main(filename, queue, config):
    """entrypoint for the singleton subprocess writing to outfile
    Use of this process enables multiple instances of a scenario without
    messing up the output file.
    """
    try:
        out_type = config['yardstick'].get('DEFAULT', {})['dispatcher']
    except KeyError:
        out_type = os.environ.get('DISPATCHER', 'file')

    conf = {
        'type': out_type.capitalize(),
        'file_path': filename
    }

    dispatcher = DispatcherBase.get(conf, config)

    while True:
        # blocks until data becomes available
        record = queue.get()
        if record == '_TERMINATE_':
            dispatcher.flush_result_data()
            break
        else:
            dispatcher.record_result_data(record)


def _execute_shell_command(command):
    """execute shell script with error handling"""
    exitcode = 0
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
    except Exception:
        exitcode = -1
        output = traceback.format_exc()
        log.error("exec command '%s' error:\n ", command)
        log.error(traceback.format_exc())

    return exitcode, output


def _single_action(seconds, command, queue):
    """entrypoint for the single action process"""
    log.debug("single action, fires after %d seconds (from now)", seconds)
    time.sleep(seconds)
    log.debug("single action: executing command: '%s'", command)
    ret_code, data = _execute_shell_command(command)
    if ret_code < 0:
        log.error("single action error! command:%s", command)
        queue.put({'single-action-data': data})
        return
    log.debug("single action data: \n%s", data)
    queue.put({'single-action-data': data})


def _periodic_action(interval, command, queue):
    """entrypoint for the periodic action process"""
    log.debug("periodic action, fires every: %d seconds", interval)
    time_spent = 0
    while True:
        time.sleep(interval)
        time_spent += interval
        log.debug("periodic action, executing command: '%s'", command)
        ret_code, data = _execute_shell_command(command)
        if ret_code < 0:
            log.error("periodic action error! command:%s", command)
            queue.put({'periodic-action-data': data})
            break
        log.debug("periodic action data: \n%s", data)
        queue.put({'periodic-action-data': data})


class Runner(object):
    queue = None
    dump_process = None
    runners = []

    @staticmethod
    def get_cls(runner_type):
        """return class of specified type"""
        for runner in utils.itersubclasses(Runner):
            if runner_type == runner.__execution_type__:
                return runner
        raise RuntimeError("No such runner_type %s" % runner_type)

    @staticmethod
    def get_types():
        """return a list of known runner type (class) names"""
        types = []
        for runner in utils.itersubclasses(Runner):
            types.append(runner)
        return types

    @staticmethod
    def get(runner_cfg, config):
        """Returns instance of a scenario runner for execution type.
        """
        # if there is no runner, start the output serializer subprocess
        if not Runner.runners:
            log.debug("Starting dump process file '%s'",
                      runner_cfg["output_filename"])
            Runner.queue = multiprocessing.Queue()
            Runner.dump_process = multiprocessing.Process(
                target=_output_serializer_main,
                name="Dumper",
                args=(runner_cfg["output_filename"], Runner.queue, config))
            Runner.dump_process.start()

        return Runner.get_cls(runner_cfg["type"])(runner_cfg, Runner.queue)

    @staticmethod
    def release_dump_process():
        """Release the dumper process"""
        log.debug("Stopping dump process")
        if Runner.dump_process:
            Runner.queue.put('_TERMINATE_')
            Runner.dump_process.join()
            Runner.dump_process = None

    @staticmethod
    def release(runner):
        """Release the runner"""
        if runner in Runner.runners:
            Runner.runners.remove(runner)

        # if this was the last runner, stop the output serializer subprocess
        if not Runner.runners:
            Runner.release_dump_process()

    @staticmethod
    def terminate(runner):
        """Terminate the runner"""
        if runner.process and runner.process.is_alive():
            runner.process.terminate()

    @staticmethod
    def terminate_all():
        """Terminate all runners (subprocesses)"""
        log.debug("Terminating all runners")

        # release dumper process as some errors before any runner is created
        if not Runner.runners:
            Runner.release_dump_process()
            return

        for runner in Runner.runners:
            log.debug("Terminating runner: %s", runner)
            if runner.process:
                runner.process.terminate()
                runner.process.join()
            if runner.periodic_action_process:
                log.debug("Terminating periodic action process")
                runner.periodic_action_process.terminate()
                runner.periodic_action_process = None
            Runner.release(runner)

    def __init__(self, config, queue):
        self.config = config
        self.periodic_action_process = None
        self.result_queue = queue
        self.output_queue = multiprocessing.Queue()
        self.process = None
        self.aborted = multiprocessing.Event()
        Runner.runners.append(self)

    def run_post_stop_action(self):
        """run a potentially configured post-stop action"""
        if "post-stop-action" in self.config:
            command = self.config["post-stop-action"]["command"]
            log.debug("post stop action: command: '%s'", command)
            ret_code, data = _execute_shell_command(command)
            if ret_code < 0:
                log.error("post action error! command:%s", command)
                self.result_queue.put({'post-stop-action-data': data})
                return
            log.debug("post-stop data: \n%s", data)
            self.result_queue.put({'post-stop-action-data': data})

    def run(self, scenario_cfg, context_cfg):
        scenario_type = scenario_cfg["type"]
        class_name = base_scenario.Scenario.get(scenario_type)
        path_split = class_name.split(".")
        module_path = ".".join(path_split[:-1])
        module = importlib.import_module(module_path)
        cls = getattr(module, path_split[-1])

        self.config['object'] = class_name
        self.aborted.clear()

        # run a potentially configured pre-start action
        if "pre-start-action" in self.config:
            command = self.config["pre-start-action"]["command"]
            log.debug("pre start action: command: '%s'", command)
            ret_code, data = _execute_shell_command(command)
            if ret_code < 0:
                log.error("pre-start action error! command:%s", command)
                self.result_queue.put({'pre-start-action-data': data})
                return
            log.debug("pre-start data: \n%s", data)
            self.result_queue.put({'pre-start-action-data': data})

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

        self._run_benchmark(cls, "run", scenario_cfg, context_cfg)

    def abort(self):
        """Abort the execution of a scenario"""
        self.aborted.set()

    def join(self, timeout=None):
        self.process.join(timeout)
        if self.periodic_action_process:
            self.periodic_action_process.terminate()
            self.periodic_action_process = None

        self.run_post_stop_action()
        return self.process.exitcode

    def get_output(self):
        result = {}
        while not self.output_queue.empty():
            result.update(self.output_queue.get())
        return result
