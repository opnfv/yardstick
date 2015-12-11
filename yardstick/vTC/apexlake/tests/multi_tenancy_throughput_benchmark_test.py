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

__author__ = 'gpetralx'


import unittest
import mock
from experimental_framework.benchmarks \
    import multi_tenancy_throughput_benchmark as bench


class MockDeploymentUnit(object):
    def deploy_heat_template(self, temp_file, stack_name, heat_param):
        pass

    def destroy_heat_template(self, stack_name):
        pass


def get_deployment_unit():
    return MockDeploymentUnit()


class TestMultiTenancyThroughputBenchmark(unittest.TestCase):
    def setUp(self):
        name = 'benchmark'
        params = dict()
        self.benchmark = bench.MultiTenancyThroughputBenchmark(name, params)

    def tearDown(self):
        pass

    def test_get_features_for_sanity(self):
        output = self.benchmark.get_features()
        self.assertIsInstance(output, dict)
        self.assertIn('parameters', output.keys())
        self.assertIn('allowed_values', output.keys())
        self.assertIn('default_values', output.keys())
        self.assertIsInstance(output['parameters'], list)
        self.assertIsInstance(output['allowed_values'], dict)
        self.assertIsInstance(output['default_values'], dict)

    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT',
                side_effect=get_deployment_unit)
    @mock.patch('experimental_framework.common.replace_in_file')
    def test_init_for_success(self, replace_in_file, deployment_unit):
        num_of_neighbours = 5
        num_of_cores = '3'
        amount_of_ram = '250M'

        self.benchmark.lua_file = 'lua_file'
        self.benchmark.results_file = 'result_file'
        self.benchmark.params['num_of_neighbours'] = str(num_of_neighbours)
        self.benchmark.params['number_of_cores'] = num_of_cores
        self.benchmark.params['amount_of_ram'] = amount_of_ram
        self.benchmark.init()

        param_1 = 'lua_file'
        param_2 = 'local out_file = ""'
        param_3 = 'local out_file = "result_file"'
        replace_in_file.assert_called_once_with(param_1, param_2, param_3)

        heat_param = dict()
        heat_param['cores'] = num_of_cores
        heat_param['memory'] = amount_of_ram
        neighbor_stack_names = list()

        deployment_unit.\
            deploy_heat_template.assert_called_with(
                self.benchmark.template_file,
                'neighbour' + str(num_of_neighbours - 1), heat_param)

        for i in range(0, num_of_neighbours):
            neighbor_stack_names.append('neighbour' + str(i))

        self.assertListEqual(neighbor_stack_names,
                             self.benchmark.neighbor_stack_names)

    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT',
                side_effect=get_deployment_unit)
    @mock.patch('experimental_framework.common.replace_in_file')
    def test_finalize_for_success(self, replace_in_file, deployment_unit):
        num_of_neighbours = 5
        self.benchmark.lua_file = 'lua_file'
        self.benchmark.results_file = 'result_file'
        self.benchmark.params['num_of_neighbours'] = str(num_of_neighbours)
        self.benchmark.neighbor_stack_names = list()
        self.benchmark.neighbor_stack_names.append(str(num_of_neighbours - 1))
        self.benchmark.finalize()

        param_1 = 'lua_file'
        param_2 = 'local out_file = "result_file"'
        param_3 = 'local out_file = ""'
        replace_in_file.assert_called_once_with(param_1, param_2, param_3)

        deployment_unit.\
            destroy_heat_template.\
            assert_called_with(str(num_of_neighbours - 1))
        self.assertListEqual(list(), self.benchmark.neighbor_stack_names)
