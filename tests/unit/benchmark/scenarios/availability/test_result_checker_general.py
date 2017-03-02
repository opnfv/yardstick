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
# .result_checker_general

from __future__ import absolute_import
import mock
import unittest
import copy

from yardstick.benchmark.scenarios.availability.result_checker import \
    result_checker_general


@mock.patch('yardstick.benchmark.scenarios.availability.result_checker.'
            'result_checker_general.ssh')
@mock.patch('yardstick.benchmark.scenarios.availability.result_checker.'
            'result_checker_general.open')
class GeneralResultCheckerTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.checker_cfg = {
            'parameter': {'processname': 'process'},
            'checker_type': 'general-result-checker',
            'condition': 'eq',
            'expectedValue': 1,
            'key': 'process-checker',
            'checker_key': 'process-checker',
            'host': 'node1'
        }

    def test__result_checker_eq(self, mock_open, mock_ssh):
        ins = result_checker_general.GeneralResultChecker(self.checker_cfg,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "1", '')
        ins.setup()
        self.assertTrue(ins.verify())

    def test__result_checker_gt(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config['condition'] = 'gt'
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "2", '')
        ins.setup()
        self.assertTrue(ins.verify())

    def test__result_checker_gt_eq(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config['condition'] = 'gt_eq'
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "1", '')
        ins.setup()
        self.assertTrue(ins.verify())

    def test__result_checker_lt(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config['condition'] = 'lt'
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "0", '')
        ins.setup()
        self.assertTrue(ins.verify())

    def test__result_checker_lt_eq(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config['condition'] = 'lt_eq'
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "1", '')
        ins.setup()
        self.assertTrue(ins.verify())

    def test__result_checker_in(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config['condition'] = 'in'
        config['expectedValue'] = "value"
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "value return", '')
        ins.setup()
        self.assertTrue(ins.verify())

    def test__result_checker_wrong(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config['condition'] = 'wrong'
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (0, "1", '')
        ins.setup()
        self.assertFalse(ins.verify())

    def test__result_checker_fail(self, mock_open, mock_ssh):
        config = copy.deepcopy(self.checker_cfg)
        config.pop('parameter')
        ins = result_checker_general.GeneralResultChecker(config,
                                                          self.context)
        mock_ssh.SSH.from_node().execute.return_value = (1, "fail", '')
        ins.setup()
        ins.verify()
