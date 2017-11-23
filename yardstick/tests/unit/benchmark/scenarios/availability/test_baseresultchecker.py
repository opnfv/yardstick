##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from yardstick.benchmark.scenarios.availability.result_checker import \
    baseresultchecker


class ResultCheckerMgrTestCase(unittest.TestCase):

    def setUp(self):
        config = {
            'checker_type': 'general-result-checker',
            'key': 'process-checker'
        }

        self.checker_configs = []
        self.checker_configs.append(config)

        self.mgr_ins = baseresultchecker.ResultCheckerMgr()

        self._mock_basechecker = mock.patch.object(baseresultchecker,
                                                   'BaseResultChecker')
        self.mock_basechecker = self._mock_basechecker.start()
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_basechecker.stop()

    def test_ResultCheckerMgr_setup_successful(self):
        self.mgr_ins.verify()

    def test_getitem_succeessful(self):
        self.mgr_ins.init_ResultChecker(self.checker_configs, None)
        _ = self.mgr_ins["process-checker"]

    def test_getitem_fail(self):
        self.mgr_ins.init_ResultChecker(self.checker_configs, None)
        with self.assertRaises(KeyError):
            _ = self.mgr_ins["checker-not-exist"]


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
        self.ins = baseresultchecker.BaseResultChecker(self.checker_cfg, None)

    def test_baseresultchecker_setup_verify_successful(self):
        self.ins.setup()
        self.ins.verify()

    def test_baseresultchecker_verfiy_pass(self):
        self.ins.setup()
        self.ins.actualResult = True
        self.ins.expectedResult = True
        self.ins.verify()

    def test_get_script_fullpath(self):
        self.ins.get_script_fullpath("test.bash")

    def test_get_resultchecker_cls_successful(self):
        baseresultchecker.BaseResultChecker.get_resultchecker_cls(
            "ResultCheckeForTest")

    def test_get_resultchecker_cls_fail(self):
        with self.assertRaises(RuntimeError):
            baseresultchecker.BaseResultChecker.get_resultchecker_cls(
                "ResultCheckeNotExist")
