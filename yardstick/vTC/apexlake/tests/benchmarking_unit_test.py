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

__author__ = 'vmriccox'


import unittest
import mock
from experimental_framework.benchmarking_unit import BenchmarkingUnit
from experimental_framework.data_manager import DataManager
from experimental_framework.deployment_unit import DeploymentUnit
import experimental_framework.common as common
from experimental_framework.benchmarks.rfc2544_throughput_benchmark import \
    RFC2544ThroughputBenchmark


class DummyDataManager(DataManager):

    def __init__(self, experiment_directory):
        self.experiment_directory = experiment_directory
        self.experiments = dict()
        self.new_exp_counter = 0
        self.add_bench_counter = 0
        self.close_experiment_1_counter = 0
        self.close_experiment_2_counter = 0
        self.generate_csv_counter = 0

    def create_new_experiment(self, experiment_name, get_counter=None):
        if not get_counter:
            self.new_exp_counter += 1
        else:
            return self.new_exp_counter

    def add_benchmark(self, experiment_name, benchmark_name, get_counter=None):
        if not get_counter:
            self.add_bench_counter += 1
        else:
            return self.add_bench_counter

    def close_experiment(self, experiment, get_counter=None):
        if get_counter:
            return [self.close_experiment_1_counter,
                    self.close_experiment_2_counter]
        if experiment == 'VTC_base_single_vm_wait_1':
            self.close_experiment_1_counter += 1
        if experiment == 'VTC_base_single_vm_wait_2':
            self.close_experiment_2_counter += 1

    def generate_result_csv_file(self, get_counter=None):
        if get_counter:
            return self.generate_csv_counter
        else:
            self.generate_csv_counter += 1

    def add_metadata(self, experiment_name, metadata):
        pass

    def add_configuration(self, experiment_name, configuration):
        pass

    def add_data_points(self, experiment_name, benchmark_name, result):
        pass


class Dummy_2544(RFC2544ThroughputBenchmark):

    def __init__(self, name, params):
        self.name = name
        self.init_counter = 0
        self.finalize_counter = 0
        self.run_counter = 0
        self.params = params

    def init(self, get_counter=None):
        if get_counter:
            return self.init_counter
        else:
            self.init_counter += 1

    def finalize(self, get_counter=None):
        if get_counter:
            return self.finalize_counter
        else:
            self.finalize_counter += 1

    def run(self, get_counter=None):
        if get_counter:
            return self.run_counter
        else:
            self.run_counter += 1
        return { 'throughput': 10 }


class DummyDeploymentUnit(DeploymentUnit):

    def __init__(self, openstack_credentials):
        pass

    def deploy_heat_template(self, template_file, stack_name, parameters,
                             attempt=0):
        return False


class TestBenchmarkingUnit(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.heat.get_all_heat_templates')
    def test___init__(self, mock_heat, mock_dep_unit, mock_data_manager,
                      mock_temp_dir, mock_time):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/results/'
        common.TEMPLATE_FILE_EXTENSION = '.ext'
        common.RESULT_DIR = 'tests/data/results/'
        heat_template_name = 'name'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = ['bench_1', 'bench_2']
        bu = BenchmarkingUnit(heat_template_name,
                               openstack_credentials,
                               heat_template_parameters,
                               iterations,
                               benchmarks)
        self.assertEqual(bu.required_benchmarks, benchmarks)
        bu.heat_template_parameters = heat_template_parameters
        mock_data_manager.assert_called_once_with('tests/data/results/12345')
        mock_dep_unit.assert_called_once_with(openstack_credentials)
        mock_heat.assert_called_once_with('tests/data/results/', '.ext')

    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_initialize_for_success(self, mock_heat, mock_dep_unit,
                                    mock_data_manager, mock_temp_dir,
                                    mock_time, mock_rfc2544):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'
        common.TEMPLATE_FILE_EXTENSION = '.yaml'
        common.RESULT_DIR = 'tests/data/results/'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit(heat_template_name,
                               openstack_credentials,
                               heat_template_parameters,
                               iterations,
                               benchmarks)
        self.assertEqual(bu.required_benchmarks, benchmarks)
        bu.heat_template_parameters = heat_template_parameters
        bu.template_files = ['VTC_base_single_vm_wait_1.yaml',
                             'VTC_base_single_vm_wait_2.yaml']
        bu.initialize()
        self.assertTrue(len(bu.benchmarks) == 1)
        self.assertEqual(bu.benchmarks[0].__class__,
                         Dummy_2544)
        self.assertEqual(bu.data_manager.create_new_experiment('', True), 2)
        self.assertEqual(bu.data_manager.add_benchmark('', '', True), 2)

    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_finalize_for_success(self, mock_heat, mock_dep_unit,
                                    mock_data_manager, mock_temp_dir,
                                    mock_time, mock_rfc2544):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'
        common.TEMPLATE_FILE_EXTENSION = '.yaml'
        common.RESULT_DIR = 'tests/data/results/'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit(heat_template_name,
                               openstack_credentials,
                               heat_template_parameters,
                               iterations,
                               benchmarks)
        bu.heat_template_parameters = heat_template_parameters
        bu.template_files = ['VTC_base_single_vm_wait_1.yaml',
                             'VTC_base_single_vm_wait_2.yaml']
        bu.finalize()
        # self.assertEqual(bu.data_manager.close_experiment('', True), [1, 1])
        self.assertEqual(bu.data_manager.generate_result_csv_file(True), 1)

    @mock.patch('experimental_framework.common.push_data_influxdb')
    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT')
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_run_benchmarks_for_success(self, mock_heat, mock_common_dep_unit,
                                        mock_dep_unit, mock_data_manager,
                                        mock_temp_dir, mock_time,
                                        mock_rfc2544, mock_log, mock_influx):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'
        common.TEMPLATE_FILE_EXTENSION = '.yaml'
        common.RESULT_DIR = 'tests/data/results/'
        common.INFLUXDB_IP = 'InfluxIP'
        common.INFLUXDB_PORT = '8086'
        common.INFLUXDB_DB_NAME = 'test_db'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit(heat_template_name,
                              openstack_credentials,
                              heat_template_parameters,
                              iterations,
                              benchmarks)
        bu.data_manager = DummyDataManager('tests/data/results/12345')
        bu.template_files = ['VTC_base_single_vm_wait_1.yaml',
                             'VTC_base_single_vm_wait_2.yaml']
        bu.benchmarks = [Dummy_2544('dummy', {'param1': 'val1'})]
        bu.run_benchmarks()
        self.assertEqual(bu.benchmarks[0].init(True), 2)
        self.assertEqual(bu.benchmarks[0].finalize(True), 2)
        self.assertEqual(bu.benchmarks[0].run(True), 2)
        expected_metric = \
            'throughput,vnic_type=direct,ram=1024,benchmark=dummy,' \
            'vcpus=2,experiment_name=VTC_base_single_vm_wait_2,' \
            'param1=val1 value=10 12345000000000'
        mock_influx.assert_called_with(expected_metric)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT')
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_run_benchmarks_2_for_success(self, mock_heat, mock_common_dep_unit,
                                        mock_dep_unit, mock_data_manager,
                                        mock_temp_dir, mock_time,
                                        mock_rfc2544, mock_log):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'
        common.TEMPLATE_FILE_EXTENSION = '.yaml'
        common.RESULT_DIR = 'tests/data/results/'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit(heat_template_name,
                              openstack_credentials,
                              heat_template_parameters,
                              iterations,
                              benchmarks)
        bu.data_manager = DummyDataManager('tests/data/results/12345')
        bu.template_files = ['VTC_base_single_vm_wait_1.yaml',
                             'VTC_base_single_vm_wait_2.yaml']
        bu.benchmarks = [Dummy_2544('dummy', dict())]
        common.DEPLOYMENT_UNIT = DummyDeploymentUnit(dict())
        bu.run_benchmarks()
        self.assertEqual(bu.benchmarks[0].init(True), 2)
        self.assertEqual(bu.benchmarks[0].finalize(True), 0)
        self.assertEqual(bu.benchmarks[0].run(True), 0)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT')
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_get_benchmark_name_for_success(self, mock_heat, mock_common_dep_unit,
                                        mock_dep_unit, mock_data_manager,
                                        mock_temp_dir, mock_time,
                                        mock_rfc2544, mock_log):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'
        common.TEMPLATE_FILE_EXTENSION = '.yaml'
        common.RESULT_DIR = 'tests/data/results/'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit(heat_template_name,
                              openstack_credentials,
                              heat_template_parameters,
                              iterations,
                              benchmarks)

        expected = 'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark_0'
        output = bu.get_benchmark_name(
            'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark')
        self.assertEqual(expected, output)

        expected = 'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark_1'
        output = bu.get_benchmark_name(
            'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark')
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT')
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_get_required_benchmarks_for_success(self, mock_heat, mock_common_dep_unit,
                                        mock_dep_unit, mock_data_manager,
                                        mock_temp_dir, mock_time,
                                        mock_rfc2544,
                                        mock_log):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'
        common.TEMPLATE_FILE_EXTENSION = '.yaml'
        common.RESULT_DIR = 'tests/data/results/'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit('',
                              openstack_credentials,
                              heat_template_parameters,
                              iterations,
                              benchmarks)

        req_benchs = \
            ['rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark']
        output = bu.get_required_benchmarks(req_benchs)
        self.assertEqual(len(req_benchs), 1)
        self.assertEqual(output[0].__class__, Dummy_2544)

    @mock.patch('experimental_framework.common.LOG')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark', side_effect=Dummy_2544)
    @mock.patch('experimental_framework.benchmarks.'
                'multi_tenancy_throughput_benchmark.'
                'MultiTenancyThroughputBenchmark')
    @mock.patch('time.time')
    @mock.patch('experimental_framework.common.get_template_dir')
    @mock.patch('experimental_framework.data_manager.DataManager',
                side_effect=DummyDataManager)
    @mock.patch('experimental_framework.common.DEPLOYMENT_UNIT')
    @mock.patch('experimental_framework.deployment_unit.DeploymentUnit')
    @mock.patch('experimental_framework.benchmarking_unit.'
                'heat.get_all_heat_templates')
    def test_get_available_test_cases_for_success(self, mock_heat, mock_common_dep_unit,
                                        mock_dep_unit, mock_data_manager,
                                        mock_temp_dir, mock_time,
                                        mock_multi, mock_rfc2544,
                                        mock_log):
        mock_heat.return_value = list()
        mock_time.return_value = '12345'
        mock_temp_dir.return_value = 'tests/data/test_templates/'

        common_template_dir = common.TEMPLATE_FILE_EXTENSION
        common.TEMPLATE_FILE_EXTENSION = '.yaml'

        common_result_dir = common.RESULT_DIR
        common.RESULT_DIR = 'tests/data/results/'

        heat_template_name = 'VTC_base_single_vm_wait_'
        openstack_credentials = {
            'name': 'aaa',
            'surname': 'bbb'
        }
        heat_template_parameters = {
            'param_1': 'name_1',
            'param_2': 'name_2'
        }
        iterations = 1
        benchmarks = [
            {
                'name':
                    'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark',
                'params': dict()
            }
        ]
        bu = BenchmarkingUnit(
            '', openstack_credentials, heat_template_parameters, iterations,
            benchmarks)
        common.init()

        expected = [
            'test_benchmark.TestBenchmark',
            'instantiation_validation_benchmark.'
            'InstantiationValidationBenchmark',
            'instantiation_validation_noisy_neighbors_benchmark.'
            'InstantiationValidationNoisyNeighborsBenchmark',
            'rfc2544_throughput_benchmark.Dummy_2544'
        ]
        output = bu.get_available_test_cases()
        self.assertEqual(expected, output)

        # def get_benchmark_name(self, name, instance=0):
        # if name + "_" + str(instance) in self.benchmark_names:
        #     instance += 1
        #     return self.get_benchmark_name(name, instance)
        # self.benchmark_names.append(name + "_" + str(instance))
        # return name + "_" + str(instance)







    # def close_experiment(self, experiment, get_counter=None):
    #     if get_counter:
    #         return [self.close_experiment_1_counter,
    #                 self.close_experiment_2_counter]
    #     if experiment == 'VTC_base_single_vm_wait_1':
    #         self.close_experiment_1_counter += 1
    #     if experiment == 'VTC_base_single_vm_wait_2':
    #         self.close_experiment_2_counter += 1
    #
    # def generate_result_csv_file(self, get_counter=None):
    #     if get_counter:
    #         return self.generate_csv_counter
    #     else:
    #         self.generate_csv_counter += 1

    # def test_extract_experiment_name_for_success(self):
    #     output = mut.BenchmarkingUnit.extract_experiment_name('test.yaml')
    #     expected = 'test'
    #     self.assertEqual(output, expected)
    #
    # def test_extract_experiment_name_2_for_success(self):
    #     output = mut.BenchmarkingUnit.extract_experiment_name('test.something.yaml')
    #     expected = 'test.something'
    #     self.assertEqual(output, expected)
    #
    # def test_extract_experiment_name_2_for_success(self):
    #     output = mut.BenchmarkingUnit.extract_experiment_name('test.something.yaml')
    #     expected = 'test.something'
    #     self.assertEqual(output, expected)
