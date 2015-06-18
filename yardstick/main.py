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

    Servers are the same as VMs (Nova call them servers in the API)

    Many tests use a client/server architecture. A test client is configured
    to use a specific test server e.g. using an IP address. This is true for
    example iperf. In some cases the test server is included in the kernel
    (ping, pktgen) and no additional software is needed on the server. In other
    cases (iperf) a server process needs to be installed and started

    One server is required to host the test client program (such as ping or
    iperf). In the task file this server is called host.

    A server can be the _target_ of a test client (think ping destination
    argument). A target server is optional but needed in most test scenarios.
    In the task file this server is called target. This is probably the same
    as DUT in existing terminology.

    Existing terminology:
    https://www.ietf.org/rfc/rfc1242.txt (throughput/latency)
    https://www.ietf.org/rfc/rfc2285.txt (DUT/SUT)

    New terminology:
    NFV TST

"""

import sys
import yaml
import atexit
import pkg_resources
import ipaddress

from yardstick.benchmark.context.model import Context
from yardstick.benchmark.runners import base as base_runner
from yardstick.cmdparser import CmdParser


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

        # TODO: support one or many contexts? Many would simpler and precise
        if "context" in cfg:
            context_cfgs = [cfg["context"]]
        else:
            context_cfgs = cfg["contexts"]

        for cfg_attrs in context_cfgs:
            context = Context()
            context.init(cfg_attrs)

        run_in_parallel = cfg.get("run_in_parallel", False)

        # TODO we need something better here, a class that represent the file
        return cfg["scenarios"], run_in_parallel


def atexit_handler():
    '''handler for process termination'''
    base_runner.Runner.terminate_all()

    if len(Context.list) > 0:
        print "Undeploying all contexts"
        for context in Context.list:
            context.undeploy()


def is_ip_addr(addr):
    '''check if string addr is an IP address'''
    try:
        ipaddress.ip_address(unicode(addr))
        return True
    except ValueError:
        return False


def run_one_scenario(scenario_cfg, output_file):
    '''run one scenario using context'''
    key_filename = pkg_resources.resource_filename(
        'yardstick.resources', 'files/yardstick_key')

    host = Context.get_server(scenario_cfg["host"])

    runner_cfg = scenario_cfg["runner"]
    runner_cfg['host'] = host.public_ip
    runner_cfg['user'] = host.context.user
    runner_cfg['key_filename'] = key_filename
    runner_cfg['output_filename'] = output_file

    if "target" in scenario_cfg:
        if is_ip_addr(scenario_cfg["target"]):
            scenario_cfg["ipaddr"] = scenario_cfg["target"]
        else:
            target = Context.get_server(scenario_cfg["target"])

            # get public IP for target server, some scenarios require it
            if target.public_ip:
                runner_cfg['target'] = target.public_ip

            # TODO scenario_cfg["ipaddr"] is bad naming
            if host.context != target.context:
                # target is in another context, get its public IP
                scenario_cfg["ipaddr"] = target.public_ip
            else:
                # target is in the same context, get its private IP
                scenario_cfg["ipaddr"] = target.private_ip

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
    scenarios, run_in_parallel = parser.parse()

    if prog_args.parse_only:
        sys.exit(0)

    for context in Context.list:
        context.deploy()

    runners = []
    if run_in_parallel:
        for scenario in scenarios:
            runner = run_one_scenario(scenario, prog_args.output_file)
            runners.append(runner)

        # Wait for runners to finish
        for runner in runners:
            runner_join(runner)
            print "Runner ended, output in", prog_args.output_file
    else:
        # run serially
        for scenario in scenarios:
            runner = run_one_scenario(scenario, prog_args.output_file)
            runner_join(runner)
            print "Runner ended, output in", prog_args.output_file

    if prog_args.keep_deploy:
        # keep deployment, forget about stack (hide it for exit handler)
        Context.list = []
    else:
        for context in Context.list:
            context.undeploy()

    print "Done, exiting"

if __name__ == '__main__':
    main()
