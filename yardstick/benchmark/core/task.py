##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import sys
import os
from collections import OrderedDict

import yaml
import atexit
import ipaddress
import time
import logging
import uuid
import collections

from six.moves import filter
from jinja2 import Environment

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.runners import base as base_runner
from yardstick.common.constants import CONF_FILE
from yardstick.common.yaml_loader import yaml_load
from yardstick.dispatcher.base import Base as DispatcherBase
from yardstick.common import constants
from yardstick.common import exceptions as y_exc
from yardstick.common import task_template
from yardstick.common import utils
from yardstick.common.html_template import report_template

output_file_default = "/tmp/yardstick.out"
test_cases_dir_default = "tests/opnfv/test_cases/"
LOG = logging.getLogger(__name__)


class Task(object):     # pragma: no cover
    """Task commands.

       Set of commands to manage benchmark tasks.
    """

    def __init__(self):
        self.contexts = []
        self.outputs = {}

    def _set_dispatchers(self, output_config):
        dispatchers = output_config.get('DEFAULT', {}).get('dispatcher',
                                                           'file')
        out_types = [s.strip() for s in dispatchers.split(',')]
        output_config['DEFAULT']['dispatcher'] = out_types

    def start(self, args, **kwargs):  # pylint: disable=unused-argument
        """Start a benchmark scenario."""

        atexit.register(self.atexit_handler)

        task_id = getattr(args, 'task_id')
        self.task_id = task_id if task_id else str(uuid.uuid4())

        self._set_log()

        try:
            output_config = utils.parse_ini_file(CONF_FILE)
        except Exception:  # pylint: disable=broad-except
            # all error will be ignore, the default value is {}
            output_config = {}

        self._init_output_config(output_config)
        self._set_output_config(output_config, args.output_file)
        LOG.debug('Output configuration is: %s', output_config)

        self._set_dispatchers(output_config)

        # update dispatcher list
        if 'file' in output_config['DEFAULT']['dispatcher']:
            result = {'status': 0, 'result': {}}
            utils.write_json_to_file(args.output_file, result)

        total_start_time = time.time()
        parser = TaskParser(args.inputfile[0])

        if args.suite:
            # 1.parse suite, return suite_params info
            task_files, task_args, task_args_fnames = parser.parse_suite()
        else:
            task_files = [parser.path]
            task_args = [args.task_args]
            task_args_fnames = [args.task_args_file]

        LOG.debug("task_files:%s, task_args:%s, task_args_fnames:%s",
                  task_files, task_args, task_args_fnames)

        if args.parse_only:
            sys.exit(0)

        testcases = {}
        tasks = self._parse_tasks(parser, task_files, args, task_args,
                                  task_args_fnames)

        # Execute task files.
        for i, _ in enumerate(task_files):
            one_task_start_time = time.time()
            self.contexts.extend(tasks[i]['contexts'])
            if not tasks[i]['meet_precondition']:
                LOG.info('"meet_precondition" is %s, please check environment',
                         tasks[i]['meet_precondition'])
                continue

            try:
                data = self._run(tasks[i]['scenarios'],
                                 tasks[i]['run_in_parallel'],
                                 output_config)
            except KeyboardInterrupt:
                raise
            except Exception:  # pylint: disable=broad-except
                LOG.error('Testcase: "%s" FAILED!!!', tasks[i]['case_name'],
                          exc_info=True)
                testcases[tasks[i]['case_name']] = {'criteria': 'FAIL',
                                                    'tc_data': []}
            else:
                LOG.info('Testcase: "%s" SUCCESS!!!', tasks[i]['case_name'])
                testcases[tasks[i]['case_name']] = {'criteria': 'PASS',
                                                    'tc_data': data}

            if args.keep_deploy:
                # keep deployment, forget about stack
                # (hide it for exit handler)
                self.contexts = []
            else:
                for context in self.contexts[::-1]:
                    context.undeploy()
                self.contexts = []
            one_task_end_time = time.time()
            LOG.info("Task %s finished in %d secs", task_files[i],
                     one_task_end_time - one_task_start_time)

        result = self._get_format_result(testcases)

        self._do_output(output_config, result)
        self._generate_reporting(result)

        total_end_time = time.time()
        LOG.info("Total finished in %d secs",
                 total_end_time - total_start_time)

        LOG.info('To generate report, execute command "yardstick report '
                 'generate %s <YAML_NAME>"', self.task_id)
        LOG.info("Task ALL DONE, exiting")
        return result

    def _generate_reporting(self, result):
        env = Environment()
        with open(constants.REPORTING_FILE, 'w') as f:
            f.write(env.from_string(report_template).render(result))

        LOG.info("Report can be found in '%s'", constants.REPORTING_FILE)

    def _set_log(self):
        log_format = '%(asctime)s %(name)s %(filename)s:%(lineno)d %(levelname)s %(message)s'
        log_formatter = logging.Formatter(log_format)

        utils.makedirs(constants.TASK_LOG_DIR)
        log_path = os.path.join(constants.TASK_LOG_DIR, '{}.log'.format(self.task_id))
        log_handler = logging.FileHandler(log_path)
        log_handler.setFormatter(log_formatter)
        log_handler.setLevel(logging.DEBUG)

        logging.root.addHandler(log_handler)

    def _init_output_config(self, output_config):
        output_config.setdefault('DEFAULT', {})
        output_config.setdefault('dispatcher_http', {})
        output_config.setdefault('dispatcher_file', {})
        output_config.setdefault('dispatcher_influxdb', {})
        output_config.setdefault('nsb', {})

    def _set_output_config(self, output_config, file_path):
        try:
            out_type = os.environ['DISPATCHER']
        except KeyError:
            output_config['DEFAULT'].setdefault('dispatcher', 'file')
        else:
            output_config['DEFAULT']['dispatcher'] = out_type

        output_config['dispatcher_file']['file_path'] = file_path

        try:
            target = os.environ['TARGET']
        except KeyError:
            pass
        else:
            k = 'dispatcher_{}'.format(output_config['DEFAULT']['dispatcher'])
            output_config[k]['target'] = target

    def _get_format_result(self, testcases):
        criteria = self._get_task_criteria(testcases)

        info = {
            'deploy_scenario': os.environ.get('DEPLOY_SCENARIO', 'unknown'),
            'installer': os.environ.get('INSTALLER_TYPE', 'unknown'),
            'pod_name': os.environ.get('NODE_NAME', 'unknown'),
            'version': os.environ.get('YARDSTICK_BRANCH', 'unknown')
        }

        result = {
            'status': 1,
            'result': {
                'criteria': criteria,
                'task_id': self.task_id,
                'info': info,
                'testcases': testcases
            }
        }

        return result

    def _get_task_criteria(self, testcases):
        criteria = any(t.get('criteria') != 'PASS' for t in testcases.values())
        if criteria:
            return 'FAIL'
        else:
            return 'PASS'

    def _do_output(self, output_config, result):
        dispatchers = DispatcherBase.get(output_config)
        dispatchers = (d for d in dispatchers if d.__dispatcher_type__ != 'Influxdb')

        for dispatcher in dispatchers:
            dispatcher.flush_result_data(result)

    def _run(self, scenarios, run_in_parallel, output_config):
        """Deploys context and calls runners"""
        for context in self.contexts:
            context.deploy()

        background_runners = []

        result = []
        # Start all background scenarios
        for scenario in filter(_is_background_scenario, scenarios):
            scenario["runner"] = dict(type="Duration", duration=1000000000)
            runner = self.run_one_scenario(scenario, output_config)
            background_runners.append(runner)

        runners = []
        if run_in_parallel:
            for scenario in scenarios:
                if not _is_background_scenario(scenario):
                    runner = self.run_one_scenario(scenario, output_config)
                    runners.append(runner)

            # Wait for runners to finish
            for runner in runners:
                status = runner_join(runner, background_runners, self.outputs, result)
                if status != 0:
                    raise RuntimeError(
                        "{0} runner status {1}".format(runner.__execution_type__, status))
                LOG.info("Runner ended")
        else:
            # run serially
            for scenario in scenarios:
                if not _is_background_scenario(scenario):
                    runner = self.run_one_scenario(scenario, output_config)
                    status = runner_join(runner, background_runners, self.outputs, result)
                    if status != 0:
                        LOG.error('Scenario NO.%s: "%s" ERROR!',
                                  scenarios.index(scenario) + 1,
                                  scenario.get('type'))
                        raise RuntimeError(
                            "{0} runner status {1}".format(runner.__execution_type__, status))
                    LOG.info("Runner ended")

        # Abort background runners
        for runner in background_runners:
            runner.abort()

        # Wait for background runners to finish
        for runner in background_runners:
            status = runner.join(self.outputs, result)
            if status is None:
                # Nuke if it did not stop nicely
                base_runner.Runner.terminate(runner)
                runner.join(self.outputs, result)
            base_runner.Runner.release(runner)

            print("Background task ended")
        return result

    def atexit_handler(self):
        """handler for process termination"""
        base_runner.Runner.terminate_all()

        if self.contexts:
            LOG.info("Undeploying all contexts")
            for context in self.contexts[::-1]:
                context.undeploy()

    def _parse_options(self, op):
        if isinstance(op, dict):
            return {k: self._parse_options(v) for k, v in op.items()}
        elif isinstance(op, list):
            return [self._parse_options(v) for v in op]
        elif isinstance(op, str):
            return self.outputs.get(op[1:]) if op.startswith('$') else op
        else:
            return op

    def _parse_tasks(self, parser, task_files, args, task_args,
                     task_args_fnames):
        tasks = []

        # Parse task_files.
        for i, _ in enumerate(task_files):
            parser.path = task_files[i]
            tasks.append(parser.parse_task(self.task_id, task_args[i],
                                           task_args_fnames[i]))
            tasks[i]['case_name'] = os.path.splitext(
                os.path.basename(task_files[i]))[0]

        if args.render_only:
            utils.makedirs(args.render_only)
            for idx, task in enumerate(tasks):
                output_file_name = os.path.abspath(os.path.join(
                    args.render_only,
                    '{0:03d}-{1}.yml'.format(idx, task['case_name'])))
                utils.write_file(output_file_name, task['rendered'])

            sys.exit(0)

        return tasks

    def run_one_scenario(self, scenario_cfg, output_config):
        """run one scenario using context"""
        runner_cfg = scenario_cfg["runner"]
        runner_cfg['output_config'] = output_config

        options = scenario_cfg.get('options', {})
        scenario_cfg['options'] = self._parse_options(options)

        # TODO support get multi hosts/vms info
        context_cfg = {}
        options = scenario_cfg.get('options') or {}
        server_name = options.get('server_name') or {}

        def config_context_target(cfg):
            target = cfg['target']
            if is_ip_addr(target):
                context_cfg['target'] = {"ipaddr": target}
            else:
                context_cfg['target'] = Context.get_server(target)
                if self._is_same_context(cfg["host"], target):
                    context_cfg['target']["ipaddr"] = context_cfg['target']["private_ip"]
                else:
                    context_cfg['target']["ipaddr"] = context_cfg['target']["ip"]

        host_name = server_name.get('host', scenario_cfg.get('host'))
        if host_name:
            context_cfg['host'] = Context.get_server(host_name)

        for item in [server_name, scenario_cfg]:
            try:
                config_context_target(item)
            except KeyError:
                LOG.debug("Got a KeyError in config_context_target(%s)", item)
            else:
                break

        if "targets" in scenario_cfg:
            ip_list = []
            for target in scenario_cfg["targets"]:
                if is_ip_addr(target):
                    ip_list.append(target)
                    context_cfg['target'] = {}
                else:
                    context_cfg['target'] = Context.get_server(target)
                    if self._is_same_context(scenario_cfg["host"],
                                             target):
                        ip_list.append(context_cfg["target"]["private_ip"])
                    else:
                        ip_list.append(context_cfg["target"]["ip"])
            context_cfg['target']['ipaddr'] = ','.join(ip_list)

        if "nodes" in scenario_cfg:
            context_cfg["nodes"] = parse_nodes_with_context(scenario_cfg)
            context_cfg["networks"] = get_networks_from_nodes(
                context_cfg["nodes"])

        runner = base_runner.Runner.get(runner_cfg)

        LOG.info("Starting runner of type '%s'", runner_cfg["type"])
        runner.run(scenario_cfg, context_cfg)

        return runner

    def _is_same_context(self, host_attr, target_attr):
        """check if two servers are in the same heat context
        host_attr: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        target_attr: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        """
        for context in self.contexts:
            if context.__context_type__ not in {"Heat", "Kubernetes"}:
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
                if (cur_pod is None) or (tc_fit_pod and cur_pod not in tc_fit_pod):
                    return False
                if (cur_installer is None) or (tc_fit_installer and cur_installer
                                               not in tc_fit_installer):
                    return False
        return True

    def _get_task_para(self, task, cur_pod):
        task_args = task.get('task_args', None)
        if task_args is not None:
            task_args = task_args.get(cur_pod, task_args.get('default'))
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
                cfg = yaml_load(stream)
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

    def _render_task(self, task_args, task_args_file):
        """Render the input task with the given arguments

        :param task_args: (dict) arguments to render the task
        :param task_args_file: (str) file containing the arguments to render
                               the task
        :return: (str) task file rendered
        """
        try:
            kw = {}
            if task_args_file:
                with open(task_args_file) as f:
                    kw.update(parse_task_args('task_args_file', f.read()))
            kw.update(parse_task_args('task_args', task_args))
        except TypeError:
            raise y_exc.TaskRenderArgumentError()

        input_task = None
        try:
            with open(self.path) as f:
                input_task = f.read()
            rendered_task = task_template.TaskTemplate.render(input_task, **kw)
            LOG.debug('Input task is:\n%s', rendered_task)
            parsed_task = yaml_load(rendered_task)
        except (IOError, OSError):
            raise y_exc.TaskReadError(task_file=self.path)
        except Exception:
            raise y_exc.TaskRenderError(input_task=input_task)

        return parsed_task, rendered_task

    def parse_task(self, task_id, task_args=None, task_args_file=None):
        """parses the task file and return an context and scenario instances"""
        LOG.info("Parsing task config: %s", self.path)

        cfg, rendered = self._render_task(task_args, task_args_file)
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

        contexts = []
        for cfg_attrs in context_cfgs:

            cfg_attrs['task_id'] = task_id
            # default to Heat context because we are testing OpenStack
            context_type = cfg_attrs.get("type", "Heat")
            context = Context.get(context_type)
            context.init(cfg_attrs)
            # Update the name in case the context has used the name_suffix
            cfg_attrs['name'] = context.name
            contexts.append(context)

        run_in_parallel = cfg.get("run_in_parallel", False)

        # add tc and task id for influxdb extended tags
        for scenario in cfg["scenarios"]:
            task_name = os.path.splitext(os.path.basename(self.path))[0]
            scenario["tc"] = task_name
            scenario["task_id"] = task_id
            # embed task path into scenario so we can load other files
            # relative to task path
            scenario["task_path"] = os.path.dirname(self.path)

            self._change_node_names(scenario, contexts)

        # TODO we need something better here, a class that represent the file
        return {'scenarios': cfg['scenarios'],
                'run_in_parallel': run_in_parallel,
                'meet_precondition': meet_precondition,
                'contexts': contexts,
                'rendered': rendered}

    @staticmethod
    def _change_node_names(scenario, contexts):
        """Change the node names in a scenario, depending on the context config

        The nodes (VMs or physical servers) are referred in the context section
        with the name of the server and the name of the context:
            <server name>.<context name>

        If the context is going to be undeployed at the end of the test, the
        task ID is suffixed to the name to avoid interferences with previous
        deployments. If the context needs to be deployed at the end of the
        test, the name assigned is kept.

        There are several places where a node name could appear in the scenario
        configuration:
        scenario:
          host: athena.demo
          target: kratos.demo
          targets:
            - athena.demo
            - kratos.demo

        scenario:
          options:
            server_name:  # JIRA: YARDSTICK-810
              host: athena.demo
              target: kratos.demo

        scenario:
          nodes:
            tg__0: tg_0.yardstick
            vnf__0: vnf_0.yardstick
        """
        def qualified_name(name):
            node_name, context_name = name.split('.')
            try:
                ctx = next((context for context in contexts
                       if context.assigned_name == context_name))
            except StopIteration:
                raise y_exc.ScenarioConfigContextNameNotFound(
                    context_name=context_name)

            return '{}.{}'.format(node_name, ctx.name)

        if 'host' in scenario:
            scenario['host'] = qualified_name(scenario['host'])
        if 'target' in scenario:
            scenario['target'] = qualified_name(scenario['target'])
        options = scenario.get('options') or {}
        server_name = options.get('server_name') or {}
        if 'host' in server_name:
            server_name['host'] = qualified_name(server_name['host'])
        if 'target' in server_name:
            server_name['target'] = qualified_name(server_name['target'])
        if 'targets' in scenario:
            for idx, target in enumerate(scenario['targets']):
                scenario['targets'][idx] = qualified_name(target)
        if 'nodes' in scenario:
            for scenario_node, target in scenario['nodes'].items():
                scenario['nodes'][scenario_node] = qualified_name(target)

    def _check_schema(self, cfg_schema, schema_type):
        """Check if config file is using the correct schema type"""

        if cfg_schema != "yardstick:" + schema_type + ":0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg_schema))

    def _check_precondition(self, cfg):
        """Check if the environment meet the precondition"""

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


def _is_background_scenario(scenario):
    if "run_in_background" in scenario:
        return scenario["run_in_background"]
    else:
        return False


def parse_nodes_with_context(scenario_cfg):
    """parse the 'nodes' fields in scenario """
    # ensure consistency in node instantiation order
    return OrderedDict((nodename, Context.get_server(scenario_cfg["nodes"][nodename]))
                       for nodename in sorted(scenario_cfg["nodes"]))


def get_networks_from_nodes(nodes):
    """parse the 'nodes' fields in scenario """
    networks = {}
    for node in nodes.values():
        if not node:
            continue
        interfaces = node.get('interfaces', {})
        for interface in interfaces.values():
            # vld_id is network_name
            network_name = interface.get('network_name')
            if not network_name:
                continue
            network = Context.get_network(network_name)
            if network:
                networks[network['name']] = network
    return networks


def runner_join(runner, background_runners, outputs, result):
    """join (wait for) a runner, exit process at runner failure
    :param background_runners:
    :type background_runners:
    :param outputs:
    :type outputs: dict
    :param result:
    :type result: list
    """
    while runner.poll() is None:
        outputs.update(runner.get_output())
        result.extend(runner.get_result())
        # drain all the background runner queues
        for background in background_runners:
            outputs.update(background.get_output())
            result.extend(background.get_result())
    status = runner.join(outputs, result)
    base_runner.Runner.release(runner)
    return status


def print_invalid_header(source_name, args):
    print("Invalid %(source)s passed:\n\n %(args)s\n"
          % {"source": source_name, "args": args})


def parse_task_args(src_name, args):
    if isinstance(args, collections.Mapping):
        return args

    try:
        kw = args and yaml_load(args)
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
