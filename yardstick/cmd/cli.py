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

import argparse
import logging

from pkg_resources import get_distribution
from argparse import RawDescriptionHelpFormatter

from yardstick.cmd.commands import task
from yardstick.cmd.commands import runner
from yardstick.cmd.commands import scenario


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

    def _get_base_parser(self):
        '''get base (top level) parser'''

        parser = argparse.ArgumentParser(
            prog='yardstick',
            formatter_class=RawDescriptionHelpFormatter,
            description=YardstickCLI.__doc__ or ''
        )

        # Global options

        parser.add_argument(
            "-V", "--version",
            help="display version",
            version=self._version,
            action="version"
        )

        parser.add_argument(
            "-d", "--debug",
            help="increase output verbosity to debug",
            action="store_true"
        )

        parser.add_argument(
            "-v", "--verbose",
            help="increase output verbosity to info",
            action="store_true"
        )

        return parser

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

    def _get_parser(self):
        '''get a command-line parser'''
        parser = self._get_base_parser()

        subparsers = parser.add_subparsers(
            title='subcommands',
        )

        # add subcommands
        for category in YardstickCLI.categories:
            command_object = YardstickCLI.categories[category]()
            desc = command_object.__doc__ or ''
            subparser = subparsers.add_parser(
                category, description=desc,
                formatter_class=RawDescriptionHelpFormatter
            )
            subparser.set_defaults(command_object=command_object)
            cmd_subparsers = subparser.add_subparsers(title='subcommands')
            self._find_actions(cmd_subparsers, command_object)

        return parser

    def main(self, argv):
        '''run the command line interface'''

        # get argument parser
        parser = self._get_parser()

        # parse command-line
        args = parser.parse_args(argv)

        # handle global opts
        logger = logging.getLogger('yardstick')
        logger.setLevel(logging.WARNING)

        if args.verbose:
            logger.getLogger('yardstick').setLevel(logging.INFO)

        if args.debug:
            logger.setLevel(logging.DEBUG)

        # dispatch to category parser
        args.func(args)
