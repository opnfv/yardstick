# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################
import uuid
import logging

from api import ApiResource
from api.database.v1.handlers import AsyncTaskHandler
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V1AsyncTask(ApiResource):

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

        asynctask_handler = AsyncTaskHandler()
        try:
            asynctask = asynctask_handler.get_task_by_taskid(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task_id')

        def _unfinished():
            return result_handler(consts.TASK_NOT_DONE, {})

        def _finished():
            return result_handler(consts.TASK_DONE, {})

        def _error():
            return result_handler(consts.TASK_FAILED, asynctask.error)

        status = asynctask.status
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
