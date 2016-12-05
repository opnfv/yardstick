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

from api.utils import influx as influx_utils
from api.utils import common as common_utils
from api.database.handlers import TasksHandler

logger = logging.getLogger(__name__)


def default(args):
    return getResult(args)


def getResult(args):
    try:
        task_id = args['task_id']

        uuid.UUID(task_id)
    except KeyError:
        message = 'task_id must be provided'
        return common_utils.error_handler(message)

    task = TasksHandler().get_task_by_taskid(task_id)

    def _unfinished():
        return common_utils.result_handler(0, [])

    def _finished():
        testcases = task.details.split(',')

        def get_data(testcase):
            query_template = "select * from %s where task_id='%s'"
            query_sql = query_template % (testcase, task_id)
            data = common_utils.translate_to_str(influx_utils.query(query_sql))
            return data

        result = {k: get_data(k) for k in testcases}

        return common_utils.result_handler(1, result)

    def _error():
        return common_utils.result_handler(2, task.error)

    try:
        status = task.status

        switcher = {
            0: _unfinished,
            1: _finished,
            2: _error
        }
        return switcher.get(status, lambda: 'nothing')()
    except IndexError:
        return common_utils.error_handler('no such task')
