#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.operation
# .operation_general

from __future__ import absolute_import
import mock
import unittest
from yardstick.benchmark.scenarios.availability.operation import \
    operation_general


@mock.patch('yardstick.benchmark.scenarios.availability.operation.'
            'operation_general.ssh')
@mock.patch('yardstick.benchmark.scenarios.availability.operation.'
            'operation_general.open')
class GeneralOperaionTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.operation_cfg = {
            'operation_type': 'general-operation',
            'action_parameter': {'ins_cup': 2},
            'rollback_parameter': {'ins_id': 'id123456'},
            'key': 'nova-create-instance',
            'operation_key': 'nova-create-instance',
            'host': 'node1',
        }
        self.operation_cfg_noparam = {
            'operation_type': 'general-operation',
            'key': 'nova-create-instance',
            'operation_key': 'nova-create-instance',
            'host': 'node1',
        }

    def test__operation_successful(self, mock_open, mock_ssh):
        ins = operation_general.GeneralOperaion(self.operation_cfg,
                                                self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "success", '')
        ins.setup()
        ins.run()
        ins.rollback()

    def test__operation_successful_noparam(self, mock_open, mock_ssh):
        ins = operation_general.GeneralOperaion(self.operation_cfg_noparam,
                                                self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "success", '')
        ins.setup()
        ins.run()
        ins.rollback()

    def test__operation_fail(self, mock_open, mock_ssh):
        ins = operation_general.GeneralOperaion(self.operation_cfg,
                                                self.context)
        mock_ssh.SSH.from_node().execute.return_value = (1, "failed", '')
        ins.setup()
        ins.run()
        ins.rollback()
