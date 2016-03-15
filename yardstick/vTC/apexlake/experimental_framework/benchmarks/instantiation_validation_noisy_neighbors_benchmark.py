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


import instantiation_validation_benchmark as base
from experimental_framework import common


NUM_OF_NEIGHBORS = 'num_of_neighbours'
AMOUNT_OF_RAM = 'amount_of_ram'
NUMBER_OF_CORES = 'number_of_cores'
NETWORK_NAME = 'network'
SUBNET_NAME = 'subnet'


class InstantiationValidationNoisyNeighborsBenchmark(
        base.InstantiationValidationBenchmark):

    def __init__(self, name, params):
        base.InstantiationValidationBenchmark.__init__(self, name, params)

        if common.RELEASE == 'liberty':
            temp_name = 'stress_workload_liberty.yaml'
        else:
            temp_name = 'stress_workload.yaml'

        self.template_file = common.get_template_dir() + \
            temp_name
        self.stack_name = 'neighbour'
        self.neighbor_stack_names = list()

    def get_features(self):
        features = super(InstantiationValidationNoisyNeighborsBenchmark,
                         self).get_features()
        features['description'] = 'Instantiation Validation Benchmark ' \
                                  'with noisy neghbors'
        features['parameters'].append(NUM_OF_NEIGHBORS)
        features['parameters'].append(AMOUNT_OF_RAM)
        features['parameters'].append(NUMBER_OF_CORES)
        features['parameters'].append(NETWORK_NAME)
        features['parameters'].append(SUBNET_NAME)
        features['allowed_values'][NUM_OF_NEIGHBORS] = \
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        features['allowed_values'][NUMBER_OF_CORES] = \
            ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        features['allowed_values'][AMOUNT_OF_RAM] = \
            ['256M', '1G', '2G', '3G', '4G', '5G', '6G', '7G', '8G', '9G',
             '10G']
        features['default_values'][NUM_OF_NEIGHBORS] = '1'
        features['default_values'][NUMBER_OF_CORES] = '1'
        features['default_values'][AMOUNT_OF_RAM] = '256M'
        features['default_values'][NETWORK_NAME] = ''
        features['default_values'][SUBNET_NAME] = ''
        return features

    def init(self):
        super(InstantiationValidationNoisyNeighborsBenchmark, self).init()
        common.replace_in_file(self.lua_file, 'local out_file = ""',
                               'local out_file = "' +
                               self.results_file + '"')
        heat_param = dict()
        heat_param['network'] = self.params[NETWORK_NAME]
        heat_param['subnet'] = self.params[SUBNET_NAME]
        heat_param['cores'] = self.params['number_of_cores']
        heat_param['memory'] = self.params['amount_of_ram']
        for i in range(0, int(self.params['num_of_neighbours'])):
            stack_name = self.stack_name + str(i)
            common.DEPLOYMENT_UNIT.deploy_heat_template(self.template_file,
                                                        stack_name,
                                                        heat_param)
            self.neighbor_stack_names.append(stack_name)

    def finalize(self):
        common.replace_in_file(self.lua_file, 'local out_file = "' +
                               self.results_file + '"',
                               'local out_file = ""')
        # destroy neighbor stacks
        for stack_name in self.neighbor_stack_names:
            common.DEPLOYMENT_UNIT.destroy_heat_template(stack_name)
        self.neighbor_stack_names = list()
