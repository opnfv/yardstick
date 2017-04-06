##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import threading
import os
import errno

from yardstick.common import constants as consts
from api.database.handlers import TasksHandler


class DaemonThread(threading.Thread):

    def __init__(self, method, args):
        super(DaemonThread, self).__init__(target=method, args=args)
        self.method = method
        self.command_list = args[0]
        self.task_dict = args[1]

    def run(self):
        self.task_dict['status'] = 0
        task_id = self.task_dict['task_id']

        try:
            task_handler = TasksHandler()
            task = task_handler.insert(self.task_dict)

            self.method(self.command_list, task_id)

            task_handler.update_status(task, 1)
        except Exception as e:
            task_handler.update_status(task, 2)
            task_handler.update_error(task, str(e))
        finally:
            _handle_testsuite_file(task_id)


def _handle_testsuite_file(task_id):
    try:
        os.remove(os.path.join(consts.TESTSUITE_DIR, task_id + '.yaml'))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
