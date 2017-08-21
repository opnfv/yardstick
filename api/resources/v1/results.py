##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging
import uuid
import json
import os

from flasgger.utils import swag_from

from api import ApiResource
from api.database.v1.handlers import TasksHandler
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler
from api.swagger import models

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


ResultModel = models.ResultModel


class V1Result(ApiResource):

    @swag_from(os.path.join(consts.REPOS_DIR, 'api/swagger/docs/results.yaml'))
    def get(self):
        args = self._get_args()

        try:
            task_id = args['task_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'task_id must be provided')

        try:
            uuid.UUID(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task_id')

        task_handler = TasksHandler()
        try:
            task = task_handler.get_task_by_taskid(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task_id')

        def _unfinished():
            return result_handler(consts.TASK_NOT_DONE, {})

        def _finished():
            if task.result:
                return result_handler(consts.TASK_DONE, json.loads(task.result))
            else:
                return result_handler(consts.TASK_DONE, {})

        def _error():
            return result_handler(consts.TASK_FAILED, task.error)

        status = task.status
        LOG.debug('Task status is: %s', status)

        if status not in [consts.TASK_NOT_DONE,
                          consts.TASK_DONE,
                          consts.TASK_FAILED]:
            return result_handler(consts.API_ERROR, 'internal server error')

        switcher = {
            consts.TASK_NOT_DONE: _unfinished,
            consts.TASK_DONE: _finished,
            consts.TASK_FAILED: _error
        }

        return switcher.get(status)()
