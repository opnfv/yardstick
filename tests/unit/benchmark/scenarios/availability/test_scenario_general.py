#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.scenario_general

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.scenario_general import \
    ScenarioGeneral


@mock.patch(
    'yardstick.benchmark.scenarios.availability.scenario_general.Director')
class ScenarioGeneralTestCase(unittest.TestCase):

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
                'steps': [
                    {
                        'actionKey': "kill-process",
                        'actionType': "attacker",
                        'index': 1},
                    {
                        'actionKey': "service-status",
                        'actionType': "monitor",
                        'index': 2}]
            }
        }

    def test_scenario_general_all_successful(self, mock_director):
        ins = ScenarioGeneral(self.scenario_cfg, None)
        ins.setup()
        ins.run({})
        ins.teardown()

    def test_scenario_general_exception(self, mock_director):
        ins = ScenarioGeneral(self.scenario_cfg, None)
        mock_obj = mock.Mock()
        mock_obj.createActionPlayer.side_effect = KeyError('Wrong')
        ins.director = mock_obj
        ins.director.data = {}
        ins.run({})
        ins.teardown()

    def test_scenario_general_case_fail(self, mock_director):
        ins = ScenarioGeneral(self.scenario_cfg, None)
        mock_obj = mock.Mock()
        mock_obj.verify.return_value = False
        ins.director = mock_obj
        ins.director.data = {}
        ins.run({})
        ins.pass_flag = True
        ins.teardown()
