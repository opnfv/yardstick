##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'task' """

from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import yaml
import atexit
import ipaddress
import time
import logging
import uuid
import errno
from six.moves import filter

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.runners import base as base_runner
from yardstick.common.task_template import TaskTemplate
from yardstick.common.utils import source_env
from yardstick.common import constants

output_file_default = "/tmp/yardstick.out"
test_cases_dir_default = "tests/opnfv/test_cases/"
LOG = logging.getLogger(__name__)


class Task(object):     # pragma: no cover
    """Task commands.

       Set of commands to manage benchmark tasks.
    """

    def start(self, args, **kwargs):
        """Start a benchmark scenario."""

        atexit.register(atexit_handler)

        self.task_id = kwargs.get('task_id', str(uuid.uuid4()))

        check_environment()

        total_start_time = time.time()
        parser = TaskParser(args.inputfile[0])

        if args.suite:
            # 1.parse suite, return suite_params info
            task_files, task_args, task_args_fnames = \
                parser.parse_suite()
        else:
            task_files = [parser.path]
            task_args = [args.task_args]
            task_args_fnames = [args.task_args_file]

        LOG.info("\ntask_files:%s, \ntask_args:%s, \ntask_args_fnames:%s",
                 task_files, task_args, task_args_fnames)

        if args.parse_only:
            sys.exit(0)

        # parse task_files
        for i in range(0, len(task_files)):
            one_task_start_time = time.time()
            parser.path = task_files[i]
            scenarios, run_in_parallel, meet_precondition = parser.parse_task(
                self.task_id, task_args[i], task_args_fnames[i])

            if not meet_precondition:
                LOG.info("meet_precondition is %s, please check envrionment",
                         meet_precondition)
                continue

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

        print("Done, exiting")

    def _run(self, scenarios, run_in_parallel, output_file):
        """Deploys context and calls runners"""
        for context in Context.list:
            context.deploy()

        background_runners = []

        # Start all background scenarios
        for scenario in filter(_is_background_scenario, scenarios):
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
                print("Runner ended, output in", output_file)
        else:
            # run serially
            for scenario in scenarios:
                if not _is_background_scenario(scenario):
                    runner = run_one_scenario(scenario, output_file)
                    runner_join(runner)
                    print("Runner ended, output in", output_file)

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
            print("Background task ended")


# TODO: Move stuff below into TaskCommands class !?


class TaskParser(object):       # pragma: no cover
    """Parser for task config files in yaml format"""

    def __init__(self, path):
        self.path = path

    def _meet_constraint(self, task, cur_pod, cur_installer):
        if "constraint" in task:
            constraint = task.get('constraint', None)
            if constraint is not None:
                tc_fit_pod = constraint.get('pod', None)
                tc_fit_installer = constraint.get('installer', None)
                LOG.info("cur_pod:%s, cur_installer:%s,tc_constraints:%s",
                         cur_pod, cur_installer, constraint)
                if cur_pod and tc_fit_pod and cur_pod not in tc_fit_pod:
                    return False
                if cur_installer and tc_fit_installer and \
                        cur_installer not in tc_fit_installer:
                    return False
        return True

    def _get_task_para(self, task, cur_pod):
        task_args = task.get('task_args', None)
        if task_args is not None:
            task_args = task_args.get(cur_pod, None)
        task_args_fnames = task.get('task_args_fnames', None)
        if task_args_fnames is not None:
            task_args_fnames = task_args_fnames.get(cur_pod, None)
        return task_args, task_args_fnames

    def parse_suite(self):
        """parse the suite file and return a list of task config file paths
           and lists of optional parameters if present"""
        LOG.info("\nParsing suite file:%s", self.path)

        try:
            with open(self.path) as stream:
                cfg = yaml.load(stream)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "suite")
        LOG.info("\nStarting scenario:%s", cfg["name"])

        test_cases_dir = cfg.get("test_cases_dir", test_cases_dir_default)
        test_cases_dir = os.path.join(constants.YARDSTICK_ROOT_PATH,
                                      test_cases_dir)
        if test_cases_dir[-1] != os.sep:
            test_cases_dir += os.sep

        cur_pod = os.environ.get('NODE_NAME', None)
        cur_installer = os.environ.get('INSTALLER_TYPE', None)

        valid_task_files = []
        valid_task_args = []
        valid_task_args_fnames = []

        for task in cfg["test_cases"]:
            # 1.check file_name
            if "file_name" in task:
                task_fname = task.get('file_name', None)
                if task_fname is None:
                    continue
            else:
                continue
            # 2.check constraint
            if self._meet_constraint(task, cur_pod, cur_installer):
                valid_task_files.append(test_cases_dir + task_fname)
            else:
                continue
            # 3.fetch task parameters
            task_args, task_args_fnames = self._get_task_para(task, cur_pod)
            valid_task_args.append(task_args)
            valid_task_args_fnames.append(task_args_fnames)

        return valid_task_files, valid_task_args, valid_task_args_fnames

    def parse_task(self, task_id, task_args=None, task_args_file=None):
        """parses the task file and return an context and scenario instances"""
        print("Parsing task config:", self.path)

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
                    print("Failed to render template:\n%(task)s\n%(err)s\n"
                          % {"task": input_task, "err": e})
                    raise e
                print("Input task is:\n%s\n" % rendered_task)

                cfg = yaml.load(rendered_task)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "task")
        meet_precondition = self._check_precondition(cfg)

        # TODO: support one or many contexts? Many would simpler and precise
        # TODO: support hybrid context type
        if "context" in cfg:
            context_cfgs = [cfg["context"]]
        elif "contexts" in cfg:
            context_cfgs = cfg["contexts"]
        else:
            context_cfgs = [{"type": "Dummy"}]

        name_suffix = '-{}'.format(task_id[:8])
        for cfg_attrs in context_cfgs:
            cfg_attrs['name'] = '{}{}'.format(cfg_attrs['name'], name_suffix)
            context_type = cfg_attrs.get("type", "Heat")
            if "Heat" == context_type and "networks" in cfg_attrs:
                # bugfix: if there are more than one network,
                # only add "external_network" on first one.
                # the name of netwrok should follow this rule:
                # test, test2, test3 ...
                # sort network with the length of network's name
                sorted_networks = sorted(cfg_attrs["networks"])
                # config external_network based on env var
                cfg_attrs["networks"][sorted_networks[0]]["external_network"] \
                    = os.environ.get("EXTERNAL_NETWORK", "net04_ext")

            context = Context.get(context_type)
            context.init(cfg_attrs)

        run_in_parallel = cfg.get("run_in_parallel", False)

        # add tc and task id for influxdb extended tags
        for scenario in cfg["scenarios"]:
            task_name = os.path.splitext(os.path.basename(self.path))[0]
            scenario["tc"] = task_name
            scenario["task_id"] = task_id

            change_server_name(scenario, name_suffix)

            try:
                for node in scenario['nodes']:
                    scenario['nodes'][node] += name_suffix
            except KeyError:
                pass

        # TODO we need something better here, a class that represent the file
        return cfg["scenarios"], run_in_parallel, meet_precondition

    def _check_schema(self, cfg_schema, schema_type):
        """Check if config file is using the correct schema type"""

        if cfg_schema != "yardstick:" + schema_type + ":0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg_schema))

    def _check_precondition(self, cfg):
        """Check if the envrionment meet the preconditon"""

        if "precondition" in cfg:
            precondition = cfg["precondition"]
            installer_type = precondition.get("installer_type", None)
            deploy_scenarios = precondition.get("deploy_scenarios", None)
            tc_fit_pods = precondition.get("pod_name", None)
            installer_type_env = os.environ.get('INSTALL_TYPE', None)
            deploy_scenario_env = os.environ.get('DEPLOY_SCENARIO', None)
            pod_name_env = os.environ.get('NODE_NAME', None)

            LOG.info("installer_type: %s, installer_type_env: %s",
                     installer_type, installer_type_env)
            LOG.info("deploy_scenarios: %s, deploy_scenario_env: %s",
                     deploy_scenarios, deploy_scenario_env)
            LOG.info("tc_fit_pods: %s, pod_name_env: %s",
                     tc_fit_pods, pod_name_env)
            if installer_type and installer_type_env:
                if installer_type_env not in installer_type:
                    return False
            if deploy_scenarios and deploy_scenario_env:
                deploy_scenarios_list = deploy_scenarios.split(',')
                for deploy_scenario in deploy_scenarios_list:
                    if deploy_scenario_env.startswith(deploy_scenario):
                        return True
                return False
            if tc_fit_pods and pod_name_env:
                if pod_name_env not in tc_fit_pods:
                    return False
        return True


def atexit_handler():
    """handler for process termination"""
    base_runner.Runner.terminate_all()

    if len(Context.list) > 0:
        print("Undeploying all contexts")
        for context in Context.list:
            context.undeploy()


def is_ip_addr(addr):
    """check if string addr is an IP address"""
    try:
        addr = addr.get('public_ip_attr', addr.get('private_ip_attr'))
    except AttributeError:
        pass

    try:
        ipaddress.ip_address(addr.encode('utf-8'))
    except ValueError:
        return False
    else:
        return True


def _is_same_heat_context(host_attr, target_attr):
    """check if two servers are in the same heat context
    host_attr: either a name for a server created by yardstick or a dict
    with attribute name mapping when using external heat templates
    target_attr: either a name for a server created by yardstick or a dict
    with attribute name mapping when using external heat templates
    """
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
    """run one scenario using context"""
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

    if "targets" in scenario_cfg:
        ip_list = []
        for target in scenario_cfg["targets"]:
            if is_ip_addr(target):
                ip_list.append(target)
                context_cfg['target'] = {}
            else:
                context_cfg['target'] = Context.get_server(target)
                if _is_same_heat_context(scenario_cfg["host"], target):
                    ip_list.append(context_cfg["target"]["private_ip"])
                else:
                    ip_list.append(context_cfg["target"]["ip"])
        context_cfg['target']['ipaddr'] = ','.join(ip_list)

    if "nodes" in scenario_cfg:
        context_cfg["nodes"] = parse_nodes_with_context(scenario_cfg)
    runner = base_runner.Runner.get(runner_cfg)

    print("Starting runner of type '%s'" % runner_cfg["type"])
    runner.run(scenario_cfg, context_cfg)

    return runner


def parse_nodes_with_context(scenario_cfg):
    """paras the 'nodes' fields in scenario """
    nodes = scenario_cfg["nodes"]

    nodes_cfg = {}
    for nodename in nodes:
        nodes_cfg[nodename] = Context.get_server(nodes[nodename])

    return nodes_cfg


def runner_join(runner):
    """join (wait for) a runner, exit process at runner failure"""
    status = runner.join()
    base_runner.Runner.release(runner)
    if status != 0:
        sys.exit("Runner failed")


def print_invalid_header(source_name, args):
    print("Invalid %(source)s passed:\n\n %(args)s\n"
          % {"source": source_name, "args": args})


def parse_task_args(src_name, args):
    try:
        kw = args and yaml.safe_load(args)
        kw = {} if kw is None else kw
    except yaml.parser.ParserError as e:
        print_invalid_header(src_name, args)
        print("%(source)s has to be YAML. Details:\n\n%(err)s\n"
              % {"source": src_name, "err": e})
        raise TypeError()

    if not isinstance(kw, dict):
        print_invalid_header(src_name, args)
        print("%(src)s had to be dict, actually %(src_type)s\n"
              % {"src": src_name, "src_type": type(kw)})
        raise TypeError()
    return kw


def check_environment():
    auth_url = os.environ.get('OS_AUTH_URL', None)
    if not auth_url:
        try:
            source_env(constants.OPENSTACK_RC_FILE)
        except IOError as e:
            if e.errno != errno.EEXIST:
                raise
            LOG.debug('OPENRC file not found')


def change_server_name(scenario, suffix):
    try:
        host = scenario['host']
    except KeyError:
        pass
    else:
        try:
            host['name'] += suffix
        except TypeError:
            scenario['host'] += suffix

    try:
        target = scenario['target']
    except KeyError:
        pass
    else:
        try:
            target['name'] += suffix
        except TypeError:
            scenario['target'] += suffix

    try:
        key = 'targets'
        scenario[key] = ['{}{}'.format(a, suffix) for a in scenario[key]]
    except KeyError:
        pass
