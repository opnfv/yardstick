##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'runner' """

from yardstick.benchmark.runners.base import Runner
from yardstick.common.utils import cliargs
from yardstick.cmd import print_hbar


class RunnerCommands(object):
    '''Runner commands.

       Set of commands to discover and display runner types.
    '''

    def do_list(self, args):
        '''List existing runner types'''
        types = Runner.get_types()
        print_hbar(78)
        print("| %-16s | %-60s" % ("Type", "Description"))
        print_hbar(78)
        for rtype in types:
            print "| %-16s | %-60s" % (rtype.__execution_type__,
                                       rtype.__doc__.split("\n")[0])
        print_hbar(78)

    @cliargs("type", type=str, help="runner type", nargs=1)
    def do_show(self, args):
        '''Show details of a specific runner type'''
        rtype = Runner.get_cls(args.type[0])
        print rtype.__doc__
