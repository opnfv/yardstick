##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import uuid
import os
import logging

from api.utils.common import result_handler
from api.utils.thread import TaskThread
from yardstick.common import constants as consts
from yardstick.benchmark.core import Param
from yardstick.benchmark.core.task import Task

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run_test_suite(args):
    try:
        suite_name = args['testsuite']
    except KeyError:
        return result_handler(consts.API_ERROR, 'testsuite must be provided')

    testsuite = os.path.join(consts.TESTSUITE_DIR,
                             '{}.yaml'.format(suite_name))

    task_id = str(uuid.uuid4())

    task_args = {
        'inputfile': [testsuite],
        'task_id': task_id,
        'suite': True
    }
    task_args.update(args.get('opts', {}))

    param = Param(task_args)
    task_thread = TaskThread(Task().start, param)
    task_thread.start()

    return result_handler(consts.API_SUCCESS, {'task_id': task_id})
