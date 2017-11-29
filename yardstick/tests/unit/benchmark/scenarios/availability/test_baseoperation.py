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

from yardstick.benchmark.scenarios.availability.operation import baseoperation


class OperationMgrTestCase(unittest.TestCase):

    def setUp(self):
        config = {
            'operation_type': 'general-operation',
            'key': 'service-status'
        }

        self.operation_configs = []
        self.operation_configs.append(config)

    @mock.patch.object(baseoperation, 'BaseOperation')
    def test_all_successful(self, *args):
        mgr_ins = baseoperation.OperationMgr()
        mgr_ins.init_operations(self.operation_configs, None)
        _ = mgr_ins["service-status"]
        mgr_ins.rollback()

    @mock.patch.object(baseoperation, 'BaseOperation')
    def test_getitem_fail(self, *args):
        mgr_ins = baseoperation.OperationMgr()
        mgr_ins.init_operations(self.operation_configs, None)
        with self.assertRaises(KeyError):
            _ = mgr_ins["operation-not-exist"]


class TestOperation(baseoperation.BaseOperation):
    __operation__type__ = "test-operation"

    def setup(self):
        pass

    def run(self):
        pass

    def rollback(self):
        pass


class BaseOperationTestCase(unittest.TestCase):

    def setUp(self):
        self.config = {
            'operation_type': 'general-operation',
            'key': 'service-status'
        }
        self.base_ins = baseoperation.BaseOperation(self.config, None)

    def test_all_successful(self):
        self.base_ins.setup()
        self.base_ins.run()
        self.base_ins.rollback()

    def test_get_script_fullpath(self):
        self.base_ins.get_script_fullpath("ha_tools/test.bash")

    # TODO(elfoley): Fix test to check on expected outputs
    # pylint: disable=unused-variable
    def test_get_operation_cls_successful(self):
        operation_ins = self.base_ins.get_operation_cls("test-operation")

    def test_get_operation_cls_fail(self):
        with self.assertRaises(RuntimeError):
            self.base_ins.get_operation_cls("operation-not-exist")
