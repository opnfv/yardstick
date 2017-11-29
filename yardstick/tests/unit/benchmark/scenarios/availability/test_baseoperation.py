#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for
# yardstick.benchmark.scenarios.availability.operation.baseoperation

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.operation import baseoperation


@mock.patch(
    'yardstick.benchmark.scenarios.availability.operation.baseoperation'
    '.BaseOperation')
class OperationMgrTestCase(unittest.TestCase):

    def setUp(self):
        config = {
            'operation_type': 'general-operation',
            'key': 'service-status'
        }

        self.operation_configs = []
        self.operation_configs.append(config)

    def test_all_successful(self, mock_operation):
        mgr_ins = baseoperation.OperationMgr()
        mgr_ins.init_operations(self.operation_configs, None)
        operation_ins = mgr_ins["service-status"]
        mgr_ins.rollback()

    def test_getitem_fail(self, mock_operation):
        mgr_ins = baseoperation.OperationMgr()
        mgr_ins.init_operations(self.operation_configs, None)
        with self.assertRaises(KeyError):
            operation_ins = mgr_ins["operation-not-exist"]


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

    def test_all_successful(self):
        base_ins = baseoperation.BaseOperation(self.config, None)
        base_ins.setup()
        base_ins.run()
        base_ins.rollback()

    def test_get_script_fullpath(self):
        base_ins = baseoperation.BaseOperation(self.config, None)
        base_ins.get_script_fullpath("ha_tools/test.bash")

    def test_get_operation_cls_successful(self):
        base_ins = baseoperation.BaseOperation(self.config, None)
        operation_ins = base_ins.get_operation_cls("test-operation")

    def test_get_operation_cls_fail(self):
        base_ins = baseoperation.BaseOperation(self.config, None)
        with self.assertRaises(RuntimeError):
            operation_ins = base_ins.get_operation_cls("operation-not-exist")
