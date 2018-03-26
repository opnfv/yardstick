#############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging

from yardstick.benchmark.core.task import Task
from yardstick.common.utils import cliargs
from yardstick.common.utils import write_json_to_file
from yardstick.cmd.commands import change_osloobj_to_paras

output_file_default = "/tmp/yardstick.out"


LOG = logging.getLogger(__name__)


class TaskCommands(object):     # pragma: no cover
    """Task commands.

       Set of commands to manage benchmark tasks.
       """

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
    @cliargs("--render-only", help="Render the tasks files, store the result "
             "in the directory given and exit", type=str, dest="render_only")
    @cliargs("--output-file", help="file where output is stored, default %s" %
             output_file_default, default=output_file_default)
    @cliargs("--suite", help="process test suite file instead of a task file",
             action="store_true")
    def do_start(self, args, **kwargs):
        param = change_osloobj_to_paras(args)
        self.output_file = param.output_file

        LOG.info('Task START')
        try:
            result = Task().start(param, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            self._write_error_data(e)
            LOG.info('Task FAILED')
            raise
        else:
            if result.get('result', {}).get('criteria') == 'PASS':
                LOG.info('Task SUCCESS')
            else:
                LOG.info('Task FAILED')
                raise RuntimeError('Task Failed')

    def _write_error_data(self, error):
        data = {'status': 2, 'result': str(error)}
        write_json_to_file(self.output_file, data)
