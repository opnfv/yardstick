##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'scenario' """

from __future__ import absolute_import
import prettytable

from yardstick.benchmark.scenarios.base import Scenario


class Scenarios(object):    # pragma: no cover
    """Scenario commands.

       Set of commands to discover and display scenario types.
    """

    def list_all(self, *args):
        """List existing scenario types"""
        types = Scenario.get_types()
        scenario_table = prettytable.PrettyTable(['Type', 'Description'])
        scenario_table.align = 'l'
        for scenario_class in types:
            scenario_table.add_row([scenario_class.get_scenario_type(),
                                    scenario_class.get_description()])
        print(scenario_table)

    def show(self, args):
        """Show details of a specific scenario type"""
        stype = Scenario.get_cls(args.type[0])
        print(stype.__doc__)
