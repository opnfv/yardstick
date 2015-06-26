##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'scenario' """

from yardstick.benchmark.scenarios.base import Scenario
from yardstick.common.utils import cliargs
from yardstick.cmd import print_hbar


class ScenarioCommands(object):
    '''Scenario commands.

       Set of commands to discover and display scenario types.
    '''

    def do_list(self, args):
        '''List existing scenario types'''
        scenarios_types = Scenario.get_types()
        print_hbar(78)
        print("| %-16s | %-60s" % ("Type", "Description"))
        print_hbar(78)
        for stype in scenarios_types:
            print("| %-16s | %-60s" % (stype.__scenario_type__,
                                       stype.__doc__.split("\n")[0]))
        print_hbar(78)

    @cliargs("type", type=str, help="runner type", nargs=1)
    def do_show(self, args):
        '''Show details of a specific scenario type'''
        stype = Scenario.get_cls(args.type[0])
        print stype.__doc__
