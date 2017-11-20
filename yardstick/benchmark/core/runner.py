##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'runner' """

from __future__ import absolute_import

import prettytable

from yardstick.benchmark.runners.base import Runner


class Runners(object):  # pragma: no cover
    """Runner commands.

       Set of commands to discover and display runner types.
    """

    def list_all(self, *args):
        """List existing runner types"""
        types = Runner.get_types()
        runner_table = prettytable.PrettyTable(['Type', 'Description'])
        runner_table.align = 'l'
        for rtype in types:
            runner_table.add_row([rtype.__execution_type__,
                                  rtype.__doc__.split("\n")[0]])
        print(runner_table)

    def show(self, args):
        """Show details of a specific runner type"""
        rtype = Runner.get_cls(args.type[0])
        print(rtype.__doc__)
