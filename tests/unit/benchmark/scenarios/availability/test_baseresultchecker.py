#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.result_checker
# .baseresultchecker

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.result_checker import \
    baseresultchecker


@mock.patch('yardstick.benchmark.scenarios.availability.result_checker'
            '.baseresultchecker.BaseResultChecker')
class ResultCheckerMgrTestCase(unittest.TestCase):

    def setUp(self):
        config = {
            'checker_type': 'general-result-checker',
            'key': 'process-checker'
        }

        self.checker_configs = []
        self.checker_configs.append(config)

    def test_ResultCheckerMgr_setup_successful(self, mock_basechacer):
        mgr_ins = baseresultchecker.ResultCheckerMgr()
        mgr_ins.init_ResultChecker(self.checker_configs, None)
        mgr_ins.verify()

    def test_getitem_succeessful(self, mock_basechacer):
        mgr_ins = baseresultchecker.ResultCheckerMgr()
        mgr_ins.init_ResultChecker(self.checker_configs, None)
        checker_ins = mgr_ins["process-checker"]

    def test_getitem_fail(self, mock_basechacer):
        mgr_ins = baseresultchecker.ResultCheckerMgr()
        mgr_ins.init_ResultChecker(self.checker_configs, None)
        with self.assertRaises(KeyError):
            checker_ins = mgr_ins["checker-not-exist"]


class BaseResultCheckerTestCase(unittest.TestCase):

    class ResultCheckeSimple(baseresultchecker.BaseResultChecker):
        __result_checker__type__ = "ResultCheckeForTest"

        def setup(self):
            self.success = False

        def verify(self):
            return self.success

    def setUp(self):
        self.checker_cfg = {
            'checker_type': 'general-result-checker',
            'key': 'process-checker'
        }

    def test_baseresultchecker_setup_verify_successful(self):
        ins = baseresultchecker.BaseResultChecker(self.checker_cfg, None)
        ins.setup()
        ins.verify()

    def test_baseresultchecker_verfiy_pass(self):
        ins = baseresultchecker.BaseResultChecker(self.checker_cfg, None)
        ins.setup()
        ins.actualResult = True
        ins.expectedResult = True
        ins.verify()

    def test_get_script_fullpath(self):
        ins = baseresultchecker.BaseResultChecker(self.checker_cfg, None)
        path = ins.get_script_fullpath("test.bash")

    def test_get_resultchecker_cls_successful(self):
        baseresultchecker.BaseResultChecker.get_resultchecker_cls(
            "ResultCheckeForTest")

    def test_get_resultchecker_cls_fail(self):
        with self.assertRaises(RuntimeError):
            baseresultchecker.BaseResultChecker.get_resultchecker_cls(
                "ResultCheckeNotExist")
