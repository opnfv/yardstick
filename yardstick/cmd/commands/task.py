##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'task' """

import sys
import yaml
import atexit
import pkg_resources
import ipaddress

from yardstick.benchmark.context.model import Context
from yardstick.benchmark.runners import base as base_runner
from yardstick.output.output import OutputMgr as output_mgr

from yardstick.common.utils import cliargs

output_file_default = "/tmp/yardstick.out"
number_of_runs_default = 1


class TaskCommands(object):
    '''Task commands.
    Set of commands to manage benchmark tasks.
    '''

    @cliargs("taskfile", type=str, help="path to taskfile", nargs=1)
    @cliargs("--keep-deploy", help="keep context deployed in cloud",
             action="store_true")
    @cliargs("--parse-only", help="parse the benchmark config file and exit",
             action="store_true")
    @cliargs("--output-file", help="file where output is stored, default %s" %
             output_file_default, default=output_file_default)
    @cliargs("--runs", help="how many times the test should be repeated, \
             default %d" % number_of_runs_default,
             type=int, default=number_of_runs_default)
    def do_start(self, args):
        '''Start a benchmark scenario.'''

        atexit.register(atexit_handler)

        output_mgr.init(args)

        parser = TaskParser(args.taskfile[0])
        scenarios, run_in_parallel = parser.parse()

        if args.parse_only:
            sys.exit(0)

        for context in Context.list:
            context.deploy()

        # Run the scenarios, repeating "runs" times

        for i in range(0, args.runs):
            runners = []
            if run_in_parallel:
                for scenario in scenarios:
                    runner = run_one_scenario(scenario)
                    runners.append(runner)

                # Wait for runners to finish
                for runner in runners:
                    runner_join(runner)
                    # TODO fix print, possibly wrong file
                    print "Runner ended, output in", \
                          output_mgr.output_descriptor
            else:
                # run serially
                for scenario in scenarios:
                    runner = run_one_scenario(scenario)
                    runner_join(runner)
                    print "Runner ended, output in", \
                          output_mgr.output_descriptor
            output_mgr.loop_done()
        output_mgr.all_done()

        if args.keep_deploy:
            # keep deployment, forget about stack (hide it for exit handler)
            Context.list = []
        else:
            for context in Context.list:
                context.undeploy()

        print "Done, exiting"


# TODO: Move stuff below into TaskCommands class !?

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

    output_mgr.shut_down()


def is_ip_addr(addr):
    '''check if string addr is an IP address'''
    try:
        ipaddress.ip_address(unicode(addr))
        return True
    except ValueError:
        return False


def run_one_scenario(scenario_cfg):
    '''run one scenario using context'''
    key_filename = pkg_resources.resource_filename(
        'yardstick.resources', 'files/yardstick_key')

    host = Context.get_server(scenario_cfg["host"])

    runner_cfg = scenario_cfg["runner"]
    runner_cfg['host'] = host.public_ip
    runner_cfg['user'] = host.context.user
    runner_cfg['key_filename'] = key_filename

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
