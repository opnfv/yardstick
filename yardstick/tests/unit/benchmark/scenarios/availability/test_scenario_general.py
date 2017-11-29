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
        self.instance = scenario_general.ScenarioGeneral(self.scenario_cfg, None)

        self._mock_director = mock.patch.object(scenario_general, 'Director')
        self.mock_director = self._mock_director.start()
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_director.stop()

    def test_scenario_general_all_successful(self):
        self.instance.setup()
        self.instance.run({})
        self.instance.teardown()

    def test_scenario_general_exception(self):
        mock_obj = mock.Mock()
        mock_obj.createActionPlayer.side_effect = KeyError('Wrong')
        self.instance.director = mock_obj
        self.instance.director.data = {}
        self.instance.run({})
        self.instance.teardown()

    def test_scenario_general_case_fail(self):
        mock_obj = mock.Mock()
        mock_obj.verify.return_value = False
        self.instance.director = mock_obj
        self.instance.director.data = {}
        self.instance.run({})
        self.instance.pass_flag = True
        self.instance.teardown()
