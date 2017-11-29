#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.director

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.director import Director


@mock.patch('yardstick.benchmark.scenarios.availability.director.basemonitor')
@mock.patch('yardstick.benchmark.scenarios.availability.director.baseattacker')
@mock.patch(
    'yardstick.benchmark.scenarios.availability.director.baseoperation')
@mock.patch(
    'yardstick.benchmark.scenarios.availability.director.baseresultchecker')
class DirectorTestCase(unittest.TestCase):

    def setUp(self):
        self.scenario_cfg = {
            'type': "general_scenario",
            'options': {
                'attackers': [{
                    'fault_type': "general-attacker",
                    'key': "kill-process"}],
                'monitors': [{
                    'monitor_type': "general-monitor",
                    'key': "service-status"}],
                'operations': [{
                    'operation_type': 'general-operation',
                    'key': 'service-status'}],
                'resultCheckers': [{
                    'checker_type': 'general-result-checker',
                    'key': 'process-checker', }],
                'steps': [
                    {
                        'actionKey': "service-status",
                        'actionType': "operation",
                        'index': 1},
                    {
                        'actionKey': "kill-process",
                        'actionType': "attacker",
                        'index': 2},
                    {
                        'actionKey': "process-checker",
                        'actionType': "resultchecker",
                        'index': 3},
                    {
                        'actionKey': "service-status",
                        'actionType': "monitor",
                        'index': 4},
                ]
            }
        }
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.ctx = {"nodes": {"node1": host}}

    def test_director_all_successful(self, mock_checer, mock_opertion,
                                     mock_attacker, mock_monitor):
        ins = Director(self.scenario_cfg, self.ctx)
        opertion_action = ins.createActionPlayer("operation", "service-status")
        attacker_action = ins.createActionPlayer("attacker", "kill-process")
        checker_action = ins.createActionPlayer("resultchecker",
                                                "process-checker")
        monitor_action = ins.createActionPlayer("monitor", "service-status")

        opertion_rollback = ins.createActionRollbacker("operation",
                                                       "service-status")
        attacker_rollback = ins.createActionRollbacker("attacker",
                                                       "kill-process")
        ins.executionSteps.append(opertion_rollback)
        ins.executionSteps.append(attacker_rollback)

        opertion_action.action()
        attacker_action.action()
        checker_action.action()
        monitor_action.action()

        attacker_rollback.rollback()
        opertion_rollback.rollback()

        ins.stopMonitors()
        ins.verify()
        ins.knockoff()

    def test_director_get_wrong_item(self, mock_checer, mock_opertion,
                                     mock_attacker, mock_monitor):
        ins = Director(self.scenario_cfg, self.ctx)
        ins.createActionPlayer("wrong_type", "wrong_key")
        ins.createActionRollbacker("wrong_type", "wrong_key")
