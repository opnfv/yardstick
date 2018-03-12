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

from yardstick.benchmark.scenarios import base
from yardstick.tests.unit import base as ut_base


class ScenarioTestCase(ut_base.BaseUnitTestCase):

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

    def test_get_types(self):
        scenario_names = set(
            scenario.__scenario_type__ for scenario in
            base.Scenario.get_types() if hasattr(scenario,
                                                 '__scenario_type__'))
        existing_scenario_class_names = {
            'Iperf3', 'CACHEstat', 'SpecCPU2006', 'Dummy', 'NSPerf', 'Parser'}
        self.assertTrue(existing_scenario_class_names.issubset(scenario_names))

    def test_get_cls_existing_scenario(self):
        scenario_name = 'NSPerf'
        scenario = base.Scenario.get_cls(scenario_name)
        self.assertEqual(scenario_name, scenario.__scenario_type__)

    def test_get_cls_non_existing_scenario(self):
        wrong_scenario_name = 'Non-existing-scenario'
        with self.assertRaises(RuntimeError) as exc:
            base.Scenario.get_cls(wrong_scenario_name)
        self.assertEqual('No such scenario type %s' % wrong_scenario_name,
                         str(exc.exception))

    def test_get_existing_scenario(self):
        scenario_name = 'NSPerf'
        scenario_module = ('yardstick.benchmark.scenarios.networking.'
                           'vnf_generic.NetworkServiceTestCase')
        self.assertEqual(scenario_module, base.Scenario.get(scenario_name))

    def test_get_non_existing_scenario(self):
        wrong_scenario_name = 'Non-existing-scenario'
        with self.assertRaises(RuntimeError) as exc:
            base.Scenario.get(wrong_scenario_name)
        self.assertEqual('No such scenario type %s' % wrong_scenario_name,
                         str(exc.exception))

    def test_scenario_abstract_class(self):
        # pylint: disable=abstract-class-instantiated
        with self.assertRaises(TypeError):
            base.Scenario()


class IterScenarioClassesTestCase(ut_base.BaseUnitTestCase):

    def test_no_scenario_type_defined(self):
        some_existing_scenario_class_names = [
            'Iperf3', 'CACHEstat', 'SpecCPU2006', 'Dummy', 'NSPerf', 'Parser']
        scenario_types = [scenario.__scenario_type__ for scenario
                          in base._iter_scenario_classes()]
        for class_name in some_existing_scenario_class_names:
            self.assertIn(class_name, scenario_types)

    def test_scenario_type_defined(self):
        some_existing_scenario_class_names = [
            'Iperf3', 'CACHEstat', 'SpecCPU2006', 'Dummy', 'NSPerf', 'Parser']
        for class_name in some_existing_scenario_class_names:
            scenario_class = next(base._iter_scenario_classes(
                scenario_type=class_name))
            self.assertEqual(class_name, scenario_class.__scenario_type__)
