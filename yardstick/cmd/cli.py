##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

'''
Command-line interface to yardstick
'''

import logging
import os
import sys

from pkg_resources import get_distribution
from argparse import RawDescriptionHelpFormatter
from oslo_config import cfg

from yardstick.cmd.commands import task
from yardstick.cmd.commands import runner
from yardstick.cmd.commands import scenario

CONF = cfg.CONF
cli_opts = [
    cfg.BoolOpt('debug',
                short='d',
                default=False,
                help='increase output verbosity to debug'),
    cfg.BoolOpt('verbose',
                short='v',
                default=False,
                help='increase output verbosity to info')
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


class YardstickCLI():
    '''Command-line interface to yardstick'''

    # Command categories
    categories = {
        'task': task.TaskCommands,
        'runner': runner.RunnerCommands,
        'scenario': scenario.ScenarioCommands
    }

    def __init__(self):
        self._version = 'yardstick version %s ' % \
            get_distribution('yardstick').version

    def _find_actions(self, subparsers, actions_module):
        '''find action methods'''
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
        '''add commands to command-line parser'''
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

    def main(self, argv):
        '''run the command line interface'''

        # register subcommands to parse additional command line arguments
        parser = lambda subparsers: self._add_command_parsers(
            YardstickCLI.categories, subparsers)
        category_opt = cfg.SubCommandOpt("category",
                                         title="Command categories",
                                         help="Available categories",
                                         handler=parser)
        CONF.register_cli_opt(category_opt)

        # load CLI args and config files
        CONF(argv, project="yardstick", version=self._version,
             default_config_files=find_config_files(CONFIG_SEARCH_PATHS))

        # handle global opts
        logger = logging.getLogger('yardstick')
        logger.setLevel(logging.WARNING)

        if CONF.verbose:
            logger.setLevel(logging.INFO)

        if CONF.debug:
            logger.setLevel(logging.DEBUG)

        # dispatch to category parser
        func = CONF.category.func
        func(CONF.category)
