# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
import mock
import os
import experimental_framework.common as common
from experimental_framework.api import FrameworkApi
from experimental_framework.benchmarking_unit import BenchmarkingUnit
import experimental_framework.benchmarks.\
    instantiation_validation_benchmark as iv


class DummyBenchmarkingUnit(BenchmarkingUnit):

    def __init__(self):
        BenchmarkingUnit.__init__(self)

    @staticmethod
    def get_available_test_cases():
        return ['BenchA', 'BenchB']

    @staticmethod
    def get_required_benchmarks(required_benchmarks):
        common.BASE_DIR = "base_dir/"
        return [iv.InstantiationValidationBenchmark('benchmark', dict())]


class DummyBenchmarkingUnit2(BenchmarkingUnit):

    counter_init = 0
    counter_finalize = 0
    counter_run = 0

    def __init__(self, base_heat_template, credentials,
                 heat_template_parameters, iterations, test_cases):
        DummyBenchmarkingUnit.counter_init = 0
        DummyBenchmarkingUnit.counter_finalize = 0
        DummyBenchmarkingUnit.counter_run = 0

    def initialize(self):
        DummyBenchmarkingUnit2.counter_init += 1

    def run_benchmarks(self):
        DummyBenchmarkingUnit2.counter_run += 1

    def finalize(self):
        DummyBenchmarkingUnit2.counter_finalize += 1


class TestGeneratesTemplate(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('experimental_framework.common.init')
    def test_init_for_success(self, mock_init):
        FrameworkApi.init()
        mock_init.assert_called_once_with(api=True)

    @mock.patch('experimental_framework.benchmarking_unit.BenchmarkingUnit.'
                'get_available_test_cases',
                side_effect=DummyBenchmarkingUnit.get_available_test_cases)
    def test_get_available_test_cases_for_success(self, mock_bench):
        expected = ['BenchA', 'BenchB']
        output = FrameworkApi.get_available_test_cases()
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.benchmarking_unit.BenchmarkingUnit.'
                'get_required_benchmarks',
                side_effect=DummyBenchmarkingUnit.get_required_benchmarks)
    def test_get_test_case_features_for_success(self, mock_get_req_bench):

        expected = dict()
        expected['description'] = 'Instantiation Validation Benchmark'
        expected['parameters'] = [
            iv.THROUGHPUT,
            iv.VLAN_SENDER,
            iv.VLAN_RECEIVER]
        expected['allowed_values'] = dict()
        expected['allowed_values'][iv.THROUGHPUT] = \
            map(str, range(0, 100))
        expected['allowed_values'][iv.VLAN_SENDER] = \
            map(str, range(-1, 4096))
        expected['allowed_values'][iv.VLAN_RECEIVER] = \
            map(str, range(-1, 4096))
        expected['default_values'] = dict()
        expected['default_values'][iv.THROUGHPUT] = '1'
        expected['default_values'][iv.VLAN_SENDER] = '-1'
        expected['default_values'][iv.VLAN_RECEIVER] = '-1'


        test_case = 'instantiation_validation_benchmark.' \
                    'InstantiationValidationBenchmark'
        output = FrameworkApi.get_test_case_features(test_case)
        self.assertEqual(expected, output)

    def test____for_failure(self):
        self.assertRaises(
            ValueError, FrameworkApi.get_test_case_features, 111)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.common.get_credentials')
    @mock.patch('experimental_framework.heat_template_generation.'
                'generates_templates')
    @mock.patch('experimental_framework.benchmarking_unit.BenchmarkingUnit',
                side_effect=DummyBenchmarkingUnit2)
    def test_execute_framework_for_success(self, mock_b_unit, mock_heat,
                                           mock_credentials, mock_log):
        common.TEMPLATE_DIR = "{}/{}/".format(
            os.getcwd(), 'tests/data/generated_templates'
        )

        test_cases = dict()
        iterations = 1
        heat_template = 'VTC_base_single_vm_wait.tmp'
        heat_template_parameters = dict()
        deployment_configuration = ''
        openstack_credentials = dict()
        openstack_credentials['ip_controller'] = ''
        openstack_credentials['heat_url'] = ''
        openstack_credentials['user'] = ''
        openstack_credentials['password'] = ''
        openstack_credentials['auth_uri'] = ''
        openstack_credentials['project'] = ''
        FrameworkApi.execute_framework(
            test_cases, iterations, heat_template,
            heat_template_parameters, deployment_configuration,
            openstack_credentials)
