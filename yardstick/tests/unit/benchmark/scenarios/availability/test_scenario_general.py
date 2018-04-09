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

from yardstick.benchmark.scenarios.availability import scenario_general

class ScenarioGeneralTestCase(unittest.TestCase):

    @mock.patch.object(scenario_general, 'Director')
    def setUp(self, *args):
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
        self.instance = scenario_general.ScenarioGeneral(self.scenario_cfg, None)
        self.instance.setup()
        self.instance.director.verify.return_value = True

    def test_scenario_general_all_successful(self):

        ret = {}
        self.instance.run(ret)
        self.instance.teardown()
        self.assertEqual(ret['sla_pass'], 1)

    def test_scenario_general_exception(self):
        self.instance.director.createActionPlayer.side_effect = KeyError('Wrong')
        self.instance.director.data = {}
        ret = {}
        self.instance.run(ret)
        self.instance.teardown()
        self.assertEqual(ret['sla_pass'], 1)

    def test_scenario_general_case_fail(self):
        self.instance.director.verify.return_value = False
        self.instance.director.data = {}
        ret = {}
        self.assertRaises(AssertionError, self.instance.run, ret)
        self.instance.teardown()
        self.assertEqual(ret['sla_pass'], 0)
