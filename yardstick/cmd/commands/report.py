##############################################################################
# Copyright (c) 2017 Rajesh Kudaka.
#
# Author: Rajesh Kudaka (4k.rajesh@gmail.com)
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'report' """

from __future__ import print_function

from __future__ import absolute_import

from yardstick.benchmark.core.report import Report
from yardstick.cmd.commands import change_osloobj_to_paras
from yardstick.common.utils import cliargs


class ReportCommands(object):   # pragma: no cover
    """Report commands.

    Set of commands to manage benchmark tasks.
    """

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def do_generate(self, args):
        """Start a benchmark scenario."""
        param = change_osloobj_to_paras(args)
        Report().generate(param)
