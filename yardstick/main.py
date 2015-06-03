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
    if HeatStack.stacks_exist():
        print "Deleting all stacks"
    HeatStack.delete_all()


def run_one_scenario(scenario_cfg, context, output_file):
    '''run one scenario using context'''
    key_filename = pkg_resources.resource_filename(
        'yardstick.resources', 'files/yardstick_key')

    '''
    Concepts:

    Servers are the same as VMs (Nova call them servers in the API)

    Many tests use a client/server architecture. A test client is configured
    to use a specific test server e.g. using an IP address. This is true for
    example iperf. In some cases the test server is included in the kernel
    (ping, pktgen) and no additional software is needed on the server. In other
    cases (iperf) a server process needs to be started

    A server can _host_ a test client program (such as ping or iperf). At least
    one server is needed for a test (meaningless otherwise)

    A server can be the _target_ of a test client (think ping destination
    argument). A target server is optional but needed in most test scenarios.
    A server can ping itself but that is not so interesting.
    '''

    host = context.get_server(scenario_cfg["host"])

    runner_cfg = scenario_cfg["runner"]
    runner_cfg['host'] = host.public_ip
    runner_cfg['user'] = context.user
    runner_cfg['key_filename'] = key_filename
    runner_cfg['output_filename'] = output_file

    if "target" in scenario_cfg:
        target = context.get_server(scenario_cfg["target"])

        # TODO(hafe) a server could be attached to several nets
        scenario_cfg["ipaddr"] = target.private_ip

        # get public IP for target server, some scenarios require it for ssh
        if target.public_ip:
            runner_cfg['target'] = target.public_ip

    runner = base_runner.Runner.get(runner_cfg)

    print "Starting runner of type '%s'" % runner_cfg["type"]
    runner.run(scenario_cfg["type"], scenario_cfg)

    return runner


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
            runner.join()
            print "Runner ended, output in", prog_args.output_file
            base_runner.Runner.release(runner)
    else:
        # run serially
        for scenario in scenarios:
            runner = run_one_scenario(scenario, context, prog_args.output_file)
            runner.join()
            print "Runner ended, output in", prog_args.output_file
            base_runner.Runner.release(runner)

    if prog_args.keep_deploy:
        # keep deployment, forget about stack (hide it for exit handler)
        context.stack = None
    else:
        context.undeploy()

    print "Done, exiting"

if __name__ == '__main__':
    main()
