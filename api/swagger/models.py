##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from flask_restful import fields
from flask_restful_swagger import swagger


# for testcases/action runTestCase action
@swagger.model
class TestCaseActionArgsOptsTaskArgModel:
    resource_fields = {
    }


@swagger.model
class TestCaseActionArgsOptsModel:
    resource_fields = {
        'task-args': TestCaseActionArgsOptsTaskArgModel,
        'keep-deploy': fields.String,
        'suite': fields.String
    }


@swagger.model
class TestCaseActionArgsModel:
    resource_fields = {
        'testcase': fields.String,
        'opts': TestCaseActionArgsOptsModel
    }


@swagger.model
class TestCaseActionModel:
    resource_fields = {
        'action': fields.String,
        'args': TestCaseActionArgsModel
    }


# for testsuite/action runTestSuite action
@swagger.model
class TestSuiteActionArgsOptsTaskArgModel:
    resource_fields = {
    }


@swagger.model
class TestSuiteActionArgsOptsModel:
    resource_fields = {
        'task-args': TestSuiteActionArgsOptsTaskArgModel,
        'keep-deploy': fields.String,
        'suite': fields.String
    }

@swagger.model
class TestSuiteActionArgsModel:
    resource_fields = {
        'testsuite': fields.String,
        'opts': TestSuiteActionArgsOptsModel
    }


@swagger.model
class TestSuiteActionModel:
    resource_fields = {
        'action': fields.String,
        'args': TestSuiteActionArgsModel
    }


# for results
@swagger.model
class ResultModel:
    resource_fields = {
        'status': fields.String,
        'result': fields.List
    }
