##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'runner' """

from __future__ import print_function

from __future__ import absolute_import
from yardstick.benchmark.core.runner import Runners
from yardstick.common.utils import cliargs
from yardstick.cmd.commands import change_osloobj_to_paras


class RunnerCommands(object):   # pragma: no cover
    """Runner commands.

       Set of commands to discover and display runner types.
    """

    def do_list(self, args):
        """List existing runner types"""
        param = change_osloobj_to_paras(args)
        Runners().list_all(param)

    @cliargs("type", type=str, help="runner type", nargs=1)
    def do_show(self, args):
        """Show details of a specific runner type"""
        param = change_osloobj_to_paras(args)
        Runners().show(param)
