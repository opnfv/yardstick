#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" yardstick - command line tool for managing benchmarks

    Example invocation:
    $ yardstick samples/ping-task.yaml
"""

import sys
import yaml
import atexit
import pkg_resources

from yardstick.benchmark.context.model import Context
from yardstick.benchmark.runners import base as base_runner
from yardstick.cmdparser import CmdParser
from yardstick.orchestrator.heat import HeatStack


class TaskParser(object):
    '''Parser for task config files in yaml format'''
    def __init__(self, path):
        self.path = path

    def parse(self):
        '''parses the task file and return an context and scenario instances'''
        print "Parsing task config:", self.path
        try:
            with open(self.path) as stream:
                cfg = yaml.load(stream)
        except IOError as ioerror:
            sys.exit(ioerror)

        if cfg["schema"] != "yardstick:task:0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg["schema"]))
        context = Context()
        context.init(cfg["context"])

        run_in_parallel = cfg.get("run_in_parallel", False)

        # TODO we need something better here, a class that represent the file
        return cfg["scenarios"], run_in_parallel, context


def atexit_handler():
    '''handler for process termination'''
    base_runner.Runner.terminate_all()

    if HeatStack.stacks_exist():
        print "Deleting all stacks"
    HeatStack.delete_all()


def run_one_scenario(scenario_cfg, context, output_file):
    '''run one scenario using context'''
    key_filename = pkg_resources.resource_filename(
        'yardstick.resources', 'files/yardstick_key')

    host = context.get_server(scenario_cfg["host"])

    runner_cfg = scenario_cfg["runner"]
    runner_cfg['host'] = host.floating_ip["ipaddr"]
    runner_cfg['user'] = context.user
    runner_cfg['key_filename'] = key_filename
    runner_cfg['output_filename'] = output_file

    target = context.get_server(scenario_cfg["target"])
    if target.floating_ip:
        runner_cfg['target'] = target.floating_ip["ipaddr"]

    # TODO hardcoded name below, a server can be attached to several nets
    scenario_cfg["ipaddr"] = target.ports["test"]["ipaddr"]

    runner = base_runner.Runner.get(runner_cfg)

    print "Starting runner of type '%s'" % runner_cfg["type"]
    runner.run(scenario_cfg["type"], scenario_cfg)

    return runner


def runner_join(runner):
    '''join (wait for) a runner, exit process at runner failure'''
    status = runner.join()
    base_runner.Runner.release(runner)
    if status != 0:
        sys.exit("Runner failed")


def main():
    '''yardstick main'''

    atexit.register(atexit_handler)

    prog_args = CmdParser().parse_args()

    parser = TaskParser(prog_args.taskfile[0])
    scenarios, run_in_parallel, context = parser.parse()

    if prog_args.parse_only:
        sys.exit(0)

    context.deploy()

    runners = []
    if run_in_parallel:
        for scenario in scenarios:
            runner = run_one_scenario(scenario, context, prog_args.output_file)
            runners.append(runner)

        # Wait for runners to finish
        for runner in runners:
            runner_join(runner)
            print "Runner ended, output in", prog_args.output_file
    else:
        # run serially
        for scenario in scenarios:
            runner = run_one_scenario(scenario, context, prog_args.output_file)
            runner_join(runner)
            print "Runner ended, output in", prog_args.output_file

    if prog_args.keep_deploy:
        # keep deployment, forget about stack (hide it for exit handler)
        context.stack = None
    else:
        context.undeploy()

    print "Done, exiting"

if __name__ == '__main__':
    main()
