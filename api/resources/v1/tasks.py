##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os
import errno
import uuid

from api import ApiResource
from api.database.v1.handlers import TasksHandler
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler


class V1TaskLog(ApiResource):
    def get(self, task_id):

        try:
            uuid.UUID(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task_id')

        task_handler = TasksHandler()
        try:
            task = task_handler.get_task_by_taskid(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task_id')

        index = int(self._get_args().get('index', 0))

        try:
            with open(os.path.join(consts.TASK_LOG_DIR, '{}.log'.format(task_id))) as f:
                f.seek(index)
                data = f.readlines()
                index = f.tell()
        except OSError as e:
            if e.errno == errno.ENOENT:
                return result_handler(consts.API_ERROR, 'log file does not exist')
            return result_handler(consts.API_ERROR, 'error with log file')

        return_data = {
            'index': index,
            'data': data
        }

        return result_handler(task.status, return_data)
