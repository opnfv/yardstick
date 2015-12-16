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
import experimental_framework.deployment_unit as deploy
import experimental_framework.benchmarks.\
    instantiation_validation_noisy_neighbors_benchmark as mut


class InstantiationValidationInitTest(unittest.TestCase):

    def setUp(self):
        name = 'instantiation_validation_noisy'
        params = {'param': 'value'}
        openstack_credentials = dict()
        openstack_credentials['ip_controller'] = ''
        openstack_credentials['project'] = ''
        openstack_credentials['auth_uri'] = ''
        openstack_credentials['user'] = ''
        openstack_credentials['heat_url'] = ''
        openstack_credentials['password'] = ''
        common.DEPLOYMENT_UNIT = deploy.DeploymentUnit(openstack_credentials)
        common.BASE_DIR = os.getcwd()
        common.TEMPLATE_DIR = 'tests/data/generated_templates'
        self.iv = mut.\
            InstantiationValidationNoisyNeighborsBenchmark(name, params)

    def tearDown(self):
        common.BASE_DIR = None
        common.TEMPLATE_DIR = None

    @mock.patch('experimental_framework.benchmarks.'
                'instantiation_validation_benchmark.'
                'InstantiationValidationBenchmark')
    @mock.patch('experimental_framework.common.get_template_dir')
    def test___init___for_success(self, mock_get_template_dir,
                                  mock_instant_validation):
        mock_get_template_dir.return_value = '/directory/'
        name = 'instantiation_validation_noisy'
        params = {'param': 'value'}
        obj = mut.InstantiationValidationNoisyNeighborsBenchmark(name, params)
        self.assertEqual(obj.template_file, '/directory/stress_workload.yaml')
        self.assertEqual(obj.stack_name, 'neighbour')
        self.assertEqual(obj.neighbor_stack_names, list())

    def test_get_features_for_success(self):
        expected = dict()
        expected['description'] = 'Instantiation Validation Benchmark with ' \
                                  'noisy neghbors'
        expected['parameters'] = list()
        expected['allowed_values'] = dict()
        expected['default_values'] = dict()
        expected['parameters'].append('throughput')
        expected['parameters'].append('vlan_sender')
        expected['parameters'].append('vlan_receiver')
        expected['parameters'].append(mut.NUM_OF_NEIGHBORS)
        expected['parameters'].append(mut.AMOUNT_OF_RAM)
        expected['parameters'].append(mut.NUMBER_OF_CORES)
        expected['allowed_values']['throughput'] = map(str, range(0, 100))
        expected['allowed_values']['vlan_sender'] = map(str, range(-1, 4096))
        expected['allowed_values']['vlan_receiver'] = map(str, range(-1, 4096))
        expected['allowed_values'][mut.NUM_OF_NEIGHBORS] = \
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        expected['allowed_values'][mut.NUMBER_OF_CORES] = \
            ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        expected['allowed_values'][mut.AMOUNT_OF_RAM] = \
            ['250M', '1G', '2G', '3G', '4G', '5G', '6G', '7G', '8G', '9G',
             '10G']
        expected['default_values']['throughput'] = '1'
        expected['default_values']['vlan_sender'] = '-1'
        expected['default_values']['vlan_receiver'] = '-1'
        expected['default_values'][mut.NUM_OF_NEIGHBORS] = '1'
        expected['default_values'][mut.NUMBER_OF_CORES] = '1'
        expected['default_values'][mut.AMOUNT_OF_RAM] = '250M'
        output = self.iv.get_features()
        self.assertEqual(expected['description'], output['description'])

        for item in output['parameters']:
            self.assertIn(item, expected['parameters'])
        for key in output['allowed_values'].keys():
            self.assertEqual(expected['allowed_values'][key],
                             output['allowed_values'][key])
        for key in output['default_values'].keys():
            self.assertEqual(expected['default_values'][key],
                             output['default_values'][key])

    @mock.patch('experimental_framework.common.replace_in_file')
    @mock.patch('experimental_framework.common.'
                'DEPLOYMENT_UNIT.deploy_heat_template')
    def test_init_for_success(self, mock_deploy_heat, mock_replace):
        self.iv.lua_file = 'file'
        self.iv.results_file = 'res_file'
        self.iv.params = {'number_of_cores': 1,
                          'amount_of_ram': 1,
                          'num_of_neighbours': 1}
        self.iv.template_file = 'template.yaml'
        self.iv.init()
        mock_replace.assert_called_once_wih('file',
                                            'local out_file = ""',
                                            'local out_file = "' +
                                            'res_file' + '"')
        mock_deploy_heat.assert_called_once_with('template.yaml',
                                                 'neighbour0',
                                                 {'cores': 1, 'memory': 1})
        self.assertEqual(self.iv.neighbor_stack_names, ['neighbour0'])

    @mock.patch('experimental_framework.common.replace_in_file')
    @mock.patch('experimental_framework.common.'
                'DEPLOYMENT_UNIT.destroy_heat_template')
    def test_finalize_for_success(self, mock_heat_destroy, mock_replace):
        self.iv.neighbor_stack_names = ['neighbor0']
        stack_name = 'neighbor0'
        self.iv.finalize()
        mock_heat_destroy.assert_called_once_with(stack_name)
        mock_replace.assert_called_once_wih('file',
                                            'local out_file = ""',
                                            'local out_file = "' +
                                            'res_file' + '"')
        self.assertEqual(self.iv.neighbor_stack_names, list())
