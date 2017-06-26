# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################
import uuid

from api.utils import common as common_utils
from api.database.v1.models import AsyncTasks


def default(args):
    return _get_status(args)


def _get_status(args):
    try:
        task_id = args['task_id']
        uuid.UUID(task_id)
    except KeyError:
        message = 'measurement and task_id must be provided'
        return common_utils.error_handler(message)

    asynctask = AsyncTasks.query.filter_by(task_id=task_id).first()

    try:
        status = asynctask.status
        error = asynctask.error if asynctask.error else []

        return common_utils.result_handler(status, error)
    except AttributeError:
        return common_utils.error_handler('no such task')
