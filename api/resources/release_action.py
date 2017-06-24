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
import json
import threading

from api.utils.common import result_handler
from yardstick.common import constants as consts
from yardstick.benchmark.core import Param
from yardstick.benchmark.core.task import Task

logger = logging.getLogger(__name__)


def runTestCase(args):
    try:
        # opts = args.get('opts', {})
        case_name = args['testcase']
    except KeyError:
        return result_handler(consts.API_ERROR, 'testcase must be provided')

    testcase = os.path.join(consts.TESTCASE_DIR, '{}.yaml'.format(case_name))

    task_id = str(uuid.uuid4())

    task_args = {
        'inputfile': [testcase],
        'task_id': task_id,
        'output-file': '/tmp/{}.out'.format(task_id)
    }

    param = Param(task_args)
    task_thread = TaskThread(Task().start, param)
    task_thread.start()

    return result_handler(consts.API_SUCCESS, {'task_id': task_id})


class TaskThread(threading.Thread):

    def __init__(self, target, args):
        super(TaskThread, self).__init__(target=target, args=args)
        self.target = target
        self.args = args

    def run(self):
        try:
            self.target(self.args)
        except Exception:
            pass
        else:
            with open('/tmp/{}.out'.format(self.args['task_id'])) as f:
                data = json.loads(f.read())
                print(data)
            os.remove('/tmp/{}.out'.format(self.args['task_id']))
