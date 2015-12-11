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


from experimental_framework.benchmarks import rfc2544_throughput_benchmark \
    as base
from experimental_framework import common


class MultiTenancyThroughputBenchmark(base.RFC2544ThroughputBenchmark):

    def __init__(self, name, params):
        base.RFC2544ThroughputBenchmark.__init__(self, name, params)
        self.template_file = "{}{}".format(common.get_template_dir(),
                                           'stress_workload.yaml')
        self.stack_name = 'neighbour'
        self.neighbor_stack_names = list()

    def get_features(self):
        features = super(MultiTenancyThroughputBenchmark, self).get_features()
        features['description'] = \
            'RFC 2544 Throughput calculation with ' \
            'memory-bound noisy neighbors'
        features['parameters'].append('num_of_neighbours')
        features['parameters'].append('amount_of_ram')
        features['parameters'].append('number_of_cores')
        features['allowed_values']['num_of_neighbours'] = \
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        features['allowed_values']['number_of_cores'] = \
            ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        features['allowed_values']['amount_of_ram'] = \
            ['250M', '1G', '2G', '3G', '4G', '5G', '6G', '7G', '8G', '9G',
             '10G']
        features['default_values']['num_of_neighbours'] = '1'
        features['default_values']['number_of_cores'] = '1'
        features['default_values']['amount_of_ram'] = '250M'
        return features

    def init(self):
        """
        Initialize the benchmark
        return: None
        """
        common.replace_in_file(self.lua_file, 'local out_file = ""',
                               'local out_file = "' +
                               self.results_file + '"')
        heat_param = dict()
        heat_param['cores'] = self.params['number_of_cores']
        heat_param['memory'] = self.params['amount_of_ram']
        for i in range(0, int(self.params['num_of_neighbours'])):
            stack_name = self.stack_name + str(i)
            common.DEPLOYMENT_UNIT.deploy_heat_template(self.template_file,
                                                        stack_name,
                                                        heat_param)
            self.neighbor_stack_names.append(stack_name)

    def finalize(self):
        """
        Finalizes the benchmark
        return: None
        """
        common.replace_in_file(self.lua_file, 'local out_file = "' +
                               self.results_file + '"',
                               'local out_file = ""')
        # destroy neighbor stacks
        for stack_name in self.neighbor_stack_names:
            common.DEPLOYMENT_UNIT.destroy_heat_template(stack_name)
        self.neighbor_stack_names = list()
