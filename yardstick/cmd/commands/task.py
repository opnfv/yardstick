##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'task' """
from __future__ import print_function

from __future__ import absolute_import
from yardstick.benchmark.core.task import Task
from yardstick.common.utils import cliargs
from yardstick.cmd.commands import change_osloobj_to_paras

output_file_default = "/tmp/yardstick.out"


class TaskCommands(object):
    '''Task commands.

       Set of commands to manage benchmark tasks.
    '''

    @cliargs("inputfile", type=str, help="path to task or suite file", nargs=1)
    @cliargs("--task-args", dest="task_args",
             help="Input task args (dict in json). These args are used"
             "to render input task that is jinja2 template.")
    @cliargs("--task-args-file", dest="task_args_file",
             help="Path to the file with input task args (dict in "
             "json/yaml). These args are used to render input"
             "task that is jinja2 template.")
    @cliargs("--keep-deploy", help="keep context deployed in cloud",
             action="store_true")
    @cliargs("--parse-only", help="parse the config file and exit",
             action="store_true")
    @cliargs("--output-file", help="file where output is stored, default %s" %
             output_file_default, default=output_file_default)
    @cliargs("--suite", help="process test suite file instead of a task file",
             action="store_true")
    def do_start(self, args, **kwargs):
        param = change_osloobj_to_paras(args)
        Task().start(param)
