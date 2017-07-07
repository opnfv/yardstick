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

from flasgger.utils import swag_from

from api import ApiResource
from api.utils.thread import TaskThread
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler
from yardstick.benchmark.core import Param
from yardstick.benchmark.core.task import Task
from api.swagger import models

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


TestSuiteActionModel = models.TestSuiteActionModel
TestSuiteActionArgsModel = models.TestSuiteActionArgsModel
TestSuiteActionArgsOptsModel = models.TestSuiteActionArgsOptsModel
TestSuiteActionArgsOptsTaskArgModel = \
    models.TestSuiteActionArgsOptsTaskArgModel


class V1Testsuite(ApiResource):

    @swag_from(os.path.join(consts.REPOS_DIR,
                            'api/swagger/docs/testsuites_action.yaml'))
    def post(self):
        return self._dispatch_post()

    def run_test_suite(self, args):
        try:
            name = args['testsuite']
        except KeyError:
            return result_handler(consts.API_ERROR,
                                  'testsuite must be provided')

        testsuite = os.path.join(consts.TESTSUITE_DIR, '{}.yaml'.format(name))

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
