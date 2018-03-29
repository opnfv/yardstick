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

import logging
import multiprocessing
import subprocess
import time
import traceback
from subprocess import CalledProcessError

import importlib

from six.moves.queue import Empty

import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base as base_scenario
from yardstick.dispatcher.base import Base as DispatcherBase

log = logging.getLogger(__name__)


def _execute_shell_command(command):
    """execute shell script with error handling"""
    exitcode = 0
    try:
        output = subprocess.check_output(command, shell=True)
    except CalledProcessError:
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
    def get(runner_cfg):
        """Returns instance of a scenario runner for execution type.
        """
        return Runner.get_cls(runner_cfg["type"])(runner_cfg)

    @staticmethod
    def release(runner):
        """Release the runner"""
        if runner in Runner.runners:
            Runner.runners.remove(runner)

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

    def __init__(self, config):
        self.task_id = None
        self.case_name = None
        self.config = config
        self.periodic_action_process = None
        self.output_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
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

    def _run_benchmark(self, cls, method_name, scenario_cfg, context_cfg):
        raise NotImplementedError

    def run(self, scenario_cfg, context_cfg):
        scenario_type = scenario_cfg["type"]
        class_name = base_scenario.Scenario.get(scenario_type)
        path_split = class_name.split(".")
        module_path = ".".join(path_split[:-1])
        module = importlib.import_module(module_path)
        cls = getattr(module, path_split[-1])

        self.config['object'] = class_name
        self.case_name = scenario_cfg['tc']
        self.task_id = scenario_cfg['task_id']
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

    QUEUE_JOIN_INTERVAL = 5

    def poll(self, timeout=QUEUE_JOIN_INTERVAL):
        self.process.join(timeout)
        return self.process.exitcode

    def join(self, outputs, result, interval=QUEUE_JOIN_INTERVAL):
        while self.process.exitcode is None:
            # drain the queue while we are running otherwise we won't terminate
            outputs.update(self.get_output())
            result.extend(self.get_result())
            self.process.join(interval)
        # drain after the process has exited
        outputs.update(self.get_output())
        result.extend(self.get_result())

        self.process.terminate()
        if self.periodic_action_process:
            self.periodic_action_process.join(1)
            self.periodic_action_process.terminate()
            self.periodic_action_process = None

        self.run_post_stop_action()
        return self.process.exitcode

    def get_output(self):
        result = {}
        while not self.output_queue.empty():
            log.debug("output_queue size %s", self.output_queue.qsize())
            try:
                result.update(self.output_queue.get(True, 1))
            except Empty:
                pass
        return result

    def get_result(self):
        result = []

        dispatcher = self.config['output_config']['DEFAULT']['dispatcher']
        output_in_influxdb = 'influxdb' in dispatcher

        while not self.result_queue.empty():
            log.debug("result_queue size %s", self.result_queue.qsize())
            try:
                one_record = self.result_queue.get(True, 1)
            except Empty:
                pass
            else:
                if output_in_influxdb:
                    self._output_to_influxdb(one_record)

                result.append(one_record)
        return result

    def _output_to_influxdb(self, record):
        dispatchers = DispatcherBase.get(self.config['output_config'])
        dispatcher = next((d for d in dispatchers if d.__dispatcher_type__ == 'Influxdb'))
        dispatcher.upload_one_record(record, self.case_name, '', task_id=self.task_id)
