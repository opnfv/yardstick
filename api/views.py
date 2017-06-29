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
import os

from flasgger.utils import swag_from

from api.base import ApiResource
from api.swagger import models

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


TestCaseActionModel = models.TestCaseActionModel
TestCaseActionArgsModel = models.TestCaseActionArgsModel
TestCaseActionArgsOptsModel = models.TestCaseActionArgsOptsModel
TestCaseActionArgsOptsTaskArgModel = models.TestCaseActionArgsOptsTaskArgModel


class Asynctask(ApiResource):
    def get(self):
        return self._dispatch_get()


class Testcases(ApiResource):
    def get(self):
        return self._dispatch_get()


class ReleaseAction(ApiResource):
    @swag_from(os.getcwd() + '/swagger/docs/release_action.yaml')
    def post(self):
        return self._dispatch_post()


class SamplesAction(ApiResource):

    def post(self):
        return self._dispatch_post()


TestSuiteActionModel = models.TestSuiteActionModel
TestSuiteActionArgsModel = models.TestSuiteActionArgsModel
TestSuiteActionArgsOptsModel = models.TestSuiteActionArgsOptsModel
TestSuiteActionArgsOptsTaskArgModel = \
    models.TestSuiteActionArgsOptsTaskArgModel


class TestsuitesAction(ApiResource):
    @swag_from(os.getcwd() + '/swagger/docs/testsuites_action.yaml')
    def post(self):
        return self._dispatch_post()


ResultModel = models.ResultModel


class Results(ApiResource):

    @swag_from(os.getcwd() + '/swagger/docs/results.yaml')
    def get(self):
        return self._dispatch_get()


class EnvAction(ApiResource):

    def post(self):
        return self._dispatch_post()


class CaseDocs(ApiResource):

    def get(self, case_name):
        return self._dispatch_get(case_name=case_name)
