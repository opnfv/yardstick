# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################

from __future__ import absolute_import
import uuid
import os
import logging

from flasgger.utils import swag_from

from yardstick.benchmark.core.testcase import Testcase
from yardstick.benchmark.core.task import Task
from yardstick.benchmark.core import Param
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler
from api.utils.thread import TaskThread
from api import ApiResource
from api.swagger import models
from api.database.v1.handlers import TasksHandler

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V1Testcase(ApiResource):

    def get(self):
        param = Param({})
        testcase_list = Testcase().list_all(param)
        return result_handler(consts.API_SUCCESS, testcase_list)


class V1CaseDocs(ApiResource):

    def get(self, case_name):
        docs_path = os.path.join(consts.DOCS_DIR, '{}.rst'.format(case_name))

        if not os.path.exists(docs_path):
            return result_handler(consts.API_ERROR, 'case not exists')

        LOG.info('Reading %s', case_name)
        with open(docs_path) as f:
            content = f.read()

        return result_handler(consts.API_SUCCESS, {'docs': content})


TestCaseActionModel = models.TestCaseActionModel
TestCaseActionArgsModel = models.TestCaseActionArgsModel
TestCaseActionArgsOptsModel = models.TestCaseActionArgsOptsModel
TestCaseActionArgsOptsTaskArgModel = models.TestCaseActionArgsOptsTaskArgModel


class V1ReleaseCase(ApiResource):

    @swag_from(os.path.join(consts.REPOS_DIR,
                            'api/swagger/docs/release_action.yaml'))
    def post(self):
        return self._dispatch_post()

    def run_test_case(self, args):
        try:
            name = args['testcase']
        except KeyError:
            return result_handler(consts.API_ERROR, 'testcase must be provided')

        testcase = os.path.join(consts.TESTCASE_DIR, '{}.yaml'.format(name))

        task_id = str(uuid.uuid4())

        task_args = {
            'inputfile': [testcase],
            'task_id': task_id
        }
        task_args.update(args.get('opts', {}))

        param = Param(task_args)
        task_thread = TaskThread(Task().start, param, TasksHandler())
        task_thread.start()

        return result_handler(consts.API_SUCCESS, {'task_id': task_id})


class V1SampleCase(ApiResource):

    def post(self):
        return self._dispatch_post()

    def run_test_case(self, args):
        try:
            name = args['testcase']
        except KeyError:
            return result_handler(consts.API_ERROR, 'testcase must be provided')

        testcase = os.path.join(consts.SAMPLE_CASE_DIR, '{}.yaml'.format(name))

        task_id = str(uuid.uuid4())

        task_args = {
            'inputfile': [testcase],
            'task_id': task_id
        }
        task_args.update(args.get('opts', {}))

        param = Param(task_args)
        task_thread = TaskThread(Task().start, param, TasksHandler())
        task_thread.start()

        return result_handler(consts.API_SUCCESS, {'task_id': task_id})
