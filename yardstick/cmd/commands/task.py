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
import os
import yaml
import atexit
import ipaddress
import time
import logging
import uuid
from itertools import ifilter

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.runners import base as base_runner
from yardstick.common.task_template import TaskTemplate
from yardstick.common.utils import cliargs

output_file_default = "/tmp/yardstick.out"
test_cases_dir_default = "tests/opnfv/test_cases/"
LOG = logging.getLogger(__name__)


class TaskCommands(object):
    '''Task commands.

       Set of commands to manage benchmark tasks.
    '''

    @cliargs("inputfile", type=str, help="path to task or suite file", nargs=1)
    @cliargs("--task-args", dest="task_args",
             help="Input task args (dict in json). These args are used"
             "to render input task that is jinja2 template.")
    @cliargs("--task-args-file", dest="task_args_file",
             help="Path to the file with input task args (dict in "
             "json/yaml). These args are used to render input"
             "task that is jinja2 template.")
    @cliargs("--keep-deploy", help="keep context deployed in cloud",
             action="store_true")
    @cliargs("--parse-only", help="parse the config file and exit",
             action="store_true")
    @cliargs("--output-file", help="file where output is stored, default %s" %
             output_file_default, default=output_file_default)
    @cliargs("--suite", help="process test suite file instead of a task file",
             action="store_true")
    def do_start(self, args):
        '''Start a benchmark scenario.'''

        atexit.register(atexit_handler)

        total_start_time = time.time()
        parser = TaskParser(args.inputfile[0])

        suite_params = {}
        if args.suite:
            suite_params = parser.parse_suite()
            test_cases_dir = suite_params["test_cases_dir"]
            if test_cases_dir[-1] != os.sep:
                test_cases_dir += os.sep
            task_files = [test_cases_dir + task
                          for task in suite_params["task_fnames"]]
        else:
            task_files = [parser.path]

        task_args = suite_params.get("task_args", [args.task_args])
        task_args_fnames = suite_params.get("task_args_fnames",
                                            [args.task_args_file])

        if args.parse_only:
            sys.exit(0)

        if os.path.isfile(args.output_file):
            os.remove(args.output_file)

        for i in range(0, len(task_files)):
            one_task_start_time = time.time()
            parser.path = task_files[i]
            task_name = os.path.splitext(os.path.basename(task_files[i]))[0]
            scenarios, run_in_parallel = parser.parse_task(task_name,
                                                           task_args[i],
                                                           task_args_fnames[i])

            self._run(scenarios, run_in_parallel, args.output_file)

            if args.keep_deploy:
                # keep deployment, forget about stack
                # (hide it for exit handler)
                Context.list = []
            else:
                for context in Context.list:
                    context.undeploy()
                Context.list = []
            one_task_end_time = time.time()
            LOG.info("task %s finished in %d secs", task_files[i],
                     one_task_end_time - one_task_start_time)

        total_end_time = time.time()
        LOG.info("total finished in %d secs",
                 total_end_time - total_start_time)

        print "Done, exiting"

    def _run(self, scenarios, run_in_parallel, output_file):
        '''Deploys context and calls runners'''
        for context in Context.list:
            context.deploy()

        background_runners = []

        # Start all background scenarios
        for scenario in ifilter(_is_background_scenario, scenarios):
            scenario["runner"] = dict(type="Duration", duration=1000000000)
            runner = run_one_scenario(scenario, output_file)
            background_runners.append(runner)

        runners = []
        if run_in_parallel:
            for scenario in scenarios:
                if not _is_background_scenario(scenario):
                    runner = run_one_scenario(scenario, output_file)
                    runners.append(runner)

            # Wait for runners to finish
            for runner in runners:
                runner_join(runner)
                print "Runner ended, output in", output_file
        else:
            # run serially
            for scenario in scenarios:
                if not _is_background_scenario(scenario):
                    runner = run_one_scenario(scenario, output_file)
                    runner_join(runner)
                    print "Runner ended, output in", output_file

        # Abort background runners
        for runner in background_runners:
            runner.abort()

        # Wait for background runners to finish
        for runner in background_runners:
            if runner.join(timeout=60) is None:
                # Nuke if it did not stop nicely
                base_runner.Runner.terminate(runner)
                runner_join(runner)
            else:
                base_runner.Runner.release(runner)
            print "Background task ended"


# TODO: Move stuff below into TaskCommands class !?


class TaskParser(object):
    '''Parser for task config files in yaml format'''
    def __init__(self, path):
        self.path = path

    def parse_suite(self):
        '''parse the suite file and return a list of task config file paths
           and lists of optional parameters if present'''
        print "Parsing suite file:", self.path

        try:
            with open(self.path) as stream:
                cfg = yaml.load(stream)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "suite")
        print "Starting suite:", cfg["name"]

        test_cases_dir = cfg.get("test_cases_dir", test_cases_dir_default)
        task_fnames = []
        task_args = []
        task_args_fnames = []

        for task in cfg["test_cases"]:
            task_fnames.append(task["file_name"])
            if "task_args" in task:
                task_args.append(task["task_args"])
            else:
                task_args.append(None)

            if "task_args_file" in task:
                task_args_fnames.append(task["task_args_file"])
            else:
                task_args_fnames.append(None)

        suite_params = {
            "test_cases_dir": test_cases_dir,
            "task_fnames": task_fnames,
            "task_args": task_args,
            "task_args_fnames": task_args_fnames
        }

        return suite_params

    def parse_task(self, task_name, task_args=None, task_args_file=None):
        '''parses the task file and return an context and scenario instances'''
        print "Parsing task config:", self.path

        try:
            kw = {}
            if task_args_file:
                with open(task_args_file) as f:
                    kw.update(parse_task_args("task_args_file", f.read()))
            kw.update(parse_task_args("task_args", task_args))
        except TypeError:
            raise TypeError()

        try:
            with open(self.path) as f:
                try:
                    input_task = f.read()
                    rendered_task = TaskTemplate.render(input_task, **kw)
                except Exception as e:
                    print(("Failed to render template:\n%(task)s\n%(err)s\n")
                          % {"task": input_task, "err": e})
                    raise e
                print(("Input task is:\n%s\n") % rendered_task)

                cfg = yaml.load(rendered_task)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "task")

        # TODO: support one or many contexts? Many would simpler and precise
        # TODO: support hybrid context type
        if "context" in cfg:
            context_cfgs = [cfg["context"]]
        elif "contexts" in cfg:
            context_cfgs = cfg["contexts"]
        else:
            context_cfgs = [{"type": "Dummy"}]

        for cfg_attrs in context_cfgs:
            context_type = cfg_attrs.get("type", "Heat")
            if "Heat" == context_type and "networks" in cfg_attrs:
                # config external_network based on env var
                for _, attrs in cfg_attrs["networks"].items():
                    attrs["external_network"] = os.environ.get(
                        'EXTERNAL_NETWORK', 'net04_ext')
            context = Context.get(context_type)
            context.init(cfg_attrs)

        run_in_parallel = cfg.get("run_in_parallel", False)

        # add tc and task id for influxdb extended tags
        task_id = str(uuid.uuid4())
        for scenario in cfg["scenarios"]:
            scenario["tc"] = task_name
            scenario["task_id"] = task_id

        # TODO we need something better here, a class that represent the file
        return cfg["scenarios"], run_in_parallel

    def _check_schema(self, cfg_schema, schema_type):
        '''Check if config file is using the correct schema type'''

        if cfg_schema != "yardstick:" + schema_type + ":0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg_schema))


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


def _is_same_heat_context(host_attr, target_attr):
    '''check if two servers are in the same heat context
    host_attr: either a name for a server created by yardstick or a dict
    with attribute name mapping when using external heat templates
    target_attr: either a name for a server created by yardstick or a dict
    with attribute name mapping when using external heat templates
    '''
    host = None
    target = None
    for context in Context.list:
        if context.__context_type__ != "Heat":
            continue

        host = context._get_server(host_attr)
        if host is None:
            continue

        target = context._get_server(target_attr)
        if target is None:
            return False

        # Both host and target is not None, then they are in the
        # same heat context.
        return True

    return False


def _is_background_scenario(scenario):
    if "run_in_background" in scenario:
        return scenario["run_in_background"]
    else:
        return False


def run_one_scenario(scenario_cfg, output_file):
    '''run one scenario using context'''
    runner_cfg = scenario_cfg["runner"]
    runner_cfg['output_filename'] = output_file

    # TODO support get multi hosts/vms info
    context_cfg = {}
    if "host" in scenario_cfg:
        context_cfg['host'] = Context.get_server(scenario_cfg["host"])

    if "target" in scenario_cfg:
        if is_ip_addr(scenario_cfg["target"]):
            context_cfg['target'] = {}
            context_cfg['target']["ipaddr"] = scenario_cfg["target"]
        else:
            context_cfg['target'] = Context.get_server(scenario_cfg["target"])
            if _is_same_heat_context(scenario_cfg["host"],
                                     scenario_cfg["target"]):
                context_cfg["target"]["ipaddr"] = \
                    context_cfg["target"]["private_ip"]
            else:
                context_cfg["target"]["ipaddr"] = \
                    context_cfg["target"]["ip"]

    if "nodes" in scenario_cfg:
        context_cfg["nodes"] = parse_nodes_with_context(scenario_cfg)
    runner = base_runner.Runner.get(runner_cfg)

    print "Starting runner of type '%s'" % runner_cfg["type"]
    runner.run(scenario_cfg, context_cfg)

    return runner


def parse_nodes_with_context(scenario_cfg):
    '''paras the 'nodes' fields in scenario '''
    nodes = scenario_cfg["nodes"]

    nodes_cfg = {}
    for nodename in nodes:
        nodes_cfg[nodename] = Context.get_server(nodes[nodename])

    return nodes_cfg


def runner_join(runner):
    '''join (wait for) a runner, exit process at runner failure'''
    status = runner.join()
    base_runner.Runner.release(runner)
    if status != 0:
        sys.exit("Runner failed")


def print_invalid_header(source_name, args):
    print(("Invalid %(source)s passed:\n\n %(args)s\n")
          % {"source": source_name, "args": args})


def parse_task_args(src_name, args):
    try:
        kw = args and yaml.safe_load(args)
        kw = {} if kw is None else kw
    except yaml.parser.ParserError as e:
        print_invalid_header(src_name, args)
        print(("%(source)s has to be YAML. Details:\n\n%(err)s\n")
              % {"source": src_name, "err": e})
        raise TypeError()

    if not isinstance(kw, dict):
        print_invalid_header(src_name, args)
        print(("%(src)s had to be dict, actually %(src_type)s\n")
              % {"src": src_name, "src_type": type(kw)})
        raise TypeError()
    return kw
