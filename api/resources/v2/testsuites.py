##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import os
import errno
import logging

import yaml

from api import ApiResource
from yardstick.common.utils import result_handler
from yardstick.common import constants as consts
from yardstick.benchmark.core.testsuite import Testsuite
from yardstick.benchmark.core import Param

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Testsuites(ApiResource):

    def get(self):
        param = Param({})
        testsuite_list = Testsuite().list_all(param)

        data = {
            'testsuites': testsuite_list
        }

        return result_handler(consts.API_SUCCESS, data)

    def post(self):
        return self._dispatch_post()

    def create_suite(self, args):
        try:
            suite_name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'name must be provided')

        try:
            testcases = args['testcases']
        except KeyError:
            return result_handler(consts.API_ERROR, 'testcases must be provided')

        testcases = [{'file_name': '{}.yaml'.format(t)} for t in testcases]

        suite = os.path.join(consts.TESTSUITE_DIR, '{}.yaml'.format(suite_name))
        suite_content = {
            'schema': 'yardstick:suite:0.1',
            'name': suite_name,
            'test_cases_dir': 'tests/opnfv/test_cases/',
            'test_cases': testcases
        }

        LOG.info('write test suite')
        with open(suite, 'w') as f:
            yaml.dump(suite_content, f, default_flow_style=False)

        return result_handler(consts.API_SUCCESS, {'suite': suite_name})


class V2Testsuite(ApiResource):

    def get(self, suite_name):
        suite_path = os.path.join(consts.TESTSUITE_DIR, '{}.yaml'.format(suite_name))
        try:
            with open(suite_path) as f:
                data = f.read()
        except IOError as e:
            if e.errno == errno.ENOENT:
                return result_handler(consts.API_ERROR, 'suite does not exist')

        return result_handler(consts.API_SUCCESS, {'testsuite': data})

    def delete(self, suite_name):
        suite_path = os.path.join(consts.TESTSUITE_DIR, '{}.yaml'.format(suite_name))
        try:
            os.remove(suite_path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return result_handler(consts.API_ERROR, 'suite does not exist')

        return result_handler(consts.API_SUCCESS, {'testsuite': suite_name})
