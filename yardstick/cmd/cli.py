##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""
Command-line interface to yardstick
"""

from __future__ import absolute_import
import logging
import os
import sys

from pkg_resources import get_distribution
from argparse import RawDescriptionHelpFormatter
from oslo_config import cfg

from yardstick import _init_logging, _LOG_STREAM_HDLR
from yardstick.cmd.commands import task
from yardstick.cmd.commands import runner
from yardstick.cmd.commands import scenario
from yardstick.cmd.commands import testcase
from yardstick.cmd.commands import plugin
from yardstick.cmd.commands import env
from yardstick.cmd.commands import report

CONF = cfg.CONF
cli_opts = [
    cfg.BoolOpt('debug',
                short='d',
                default=False,
                help='increase output verbosity to debug')
]
CONF.register_cli_opts(cli_opts)

CONFIG_SEARCH_PATHS = [sys.prefix + "/etc/yardstick",
                       "~/.yardstick",
                       "/etc/yardstick"]


def find_config_files(path_list):
    for path in path_list:
        abspath = os.path.abspath(os.path.expanduser(path))
        confname = abspath + "/yardstick.conf"
        if os.path.isfile(confname):
            return [confname]

    return None


class YardstickCLI():   # pragma: no cover
    """Command-line interface to yardstick"""

    # Command categories
    categories = {
        'task': task.TaskCommands,
        'runner': runner.RunnerCommands,
        'scenario': scenario.ScenarioCommands,
        'testcase': testcase.TestcaseCommands,
        'plugin': plugin.PluginCommands,
        'env': env.EnvCommand,
        'report': report.ReportCommands
    }

    def __init__(self):
        self.opts = []
        self._version = 'yardstick version %s ' % \
            get_distribution('yardstick').version

    def _find_actions(self, subparsers, actions_module):
        """find action methods"""
        # Find action methods inside actions_module and
        # add them to the command parser.
        # The 'actions_module' argument may be a class
        # or module. Action methods start with 'do_'
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            arguments = getattr(callback, 'arguments', [])
            subparser = subparsers.add_parser(
                command,
                description=desc
            )
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def _add_command_parsers(self, categories, subparsers):
        """add commands to command-line parser"""
        for category in categories:
            command_object = categories[category]()
            desc = command_object.__doc__ or ''
            subparser = subparsers.add_parser(
                category, description=desc,
                formatter_class=RawDescriptionHelpFormatter
            )
            subparser.set_defaults(command_object=command_object)
            cmd_subparsers = subparser.add_subparsers(title='subcommands')
            self._find_actions(cmd_subparsers, command_object)

    def _register_cli_opt(self):

        # register subcommands to parse additional command line arguments
        def parser(subparsers):
            self._add_command_parsers(YardstickCLI.categories, subparsers)

        category_opt = cfg.SubCommandOpt("category",
                                         title="Command categories",
                                         help="Available categories",
                                         handler=parser)
        self._register_opt(category_opt)

    def _register_opt(self, opt):

        CONF.register_cli_opt(opt)
        self.opts.append(opt)

    def _load_cli_config(self, argv):

        # load CLI args and config files
        CONF(argv, project="yardstick", version=self._version,
             default_config_files=find_config_files(CONFIG_SEARCH_PATHS))

    def _handle_global_opts(self):

        _init_logging()
        if CONF.debug:
            _LOG_STREAM_HDLR.setLevel(logging.DEBUG)

    def _dispatch_func_notask(self):

        # dispatch to category parser
        func = CONF.category.func
        func(CONF.category)

    def _dispatch_func_task(self, task_id):

        # dispatch to category parser
        func = CONF.category.func
        func(CONF.category, task_id=task_id)

    def _clear_config_opts(self):

        CONF.clear()
        CONF.unregister_opts(self.opts)

    def main(self, argv):    # pragma: no cover
        """run the command line interface"""
        try:
            self._register_cli_opt()

            self._load_cli_config(argv)

            self._handle_global_opts()

            self._dispatch_func_notask()
        finally:
            self._clear_config_opts()

    def api(self, argv, task_id):    # pragma: no cover
        """run the api interface"""
        try:
            self._register_cli_opt()

            self._load_cli_config(argv)

            self._handle_global_opts()

            self._dispatch_func_task(task_id)
        finally:
            self._clear_config_opts()
