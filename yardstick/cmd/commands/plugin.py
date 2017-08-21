##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'plugin' """

from __future__ import print_function

from __future__ import absolute_import
from yardstick.benchmark.core.plugin import Plugin
from yardstick.common.utils import cliargs
from yardstick.cmd.commands import change_osloobj_to_paras


class PluginCommands(object):   # pragma: no cover
    """Plugin commands.

       Set of commands to manage plugins.
    """

    @cliargs("input_file", type=str, help="path to plugin configuration file",
             nargs=1)
    def do_install(self, args):
        """Install a plugin."""
        param = change_osloobj_to_paras(args)
        Plugin().install(param)

    @cliargs("input_file", type=str, help="path to plugin configuration file",
             nargs=1)
    def do_remove(self, args):
        """Remove a plugin."""
        param = change_osloobj_to_paras(args)
        Plugin().remove(param)
