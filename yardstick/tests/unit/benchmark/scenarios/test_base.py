# Copyright 2017: Intel Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import unittest

from yardstick.benchmark.scenarios import base


class ScenarioTestCase(unittest.TestCase):

    def test_get_scenario_type(self):
        scenario_type = 'dummy scenario'

        class DummyScenario(base.Scenario):
            __scenario_type__ = scenario_type

        self.assertEqual(scenario_type, DummyScenario.get_scenario_type())

    def test_get_scenario_type_not_defined(self):
        class DummyScenario(base.Scenario):
            pass

        self.assertEqual(str(None), DummyScenario.get_scenario_type())

    def test_get_description(self):
        docstring = """First line
            Second line
            Third line
        """

        class DummyScenario(base.Scenario):
            __doc__ = docstring

        self.assertEqual(docstring.splitlines()[0],
                         DummyScenario.get_description())

    def test_get_description_empty(self):
        class DummyScenario(base.Scenario):
            pass

        self.assertEqual(str(None), DummyScenario.get_description())
