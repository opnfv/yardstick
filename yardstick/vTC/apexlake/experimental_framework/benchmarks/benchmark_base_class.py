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


import abc


class BenchmarkBaseClass(object):
    '''
    This class represents a Benchmark that we want to run on the platform.
    One of them will be the calculation of the throughput changing the
    configuration parameters
    '''

    def __init__(self, name, params):
        if not params:
            params = dict()
        if not isinstance(params, dict):
            raise ValueError("Parameters need to be provided in a dict")

        for param in self.get_features()['parameters']:
            if param not in params.keys():
                params[param] = self.get_features()['default_values'][param]

        for param in self.get_features()['parameters']:
            if params[param] not in \
                    (self.get_features())['allowed_values'][param]:
                raise ValueError('Value of parameter "' + param +
                                 '" is not allowed')
        self.name = name
        self.params = params

    def get_name(self):
        return self.name

    def get_features(self):
        features = dict()
        features['description'] = 'Please implement the method ' \
                                  '"get_features" for your benchmark'
        features['parameters'] = list()
        features['allowed_values'] = dict()
        features['default_values'] = dict()
        return features

    @abc.abstractmethod
    def init(self):
        """
        Initializes the benchmark
        :return:
        """
        raise NotImplementedError("Subclass must implement abstract method")

    @abc.abstractmethod
    def finalize(self):
        """
        Finalizes the benchmark
        :return:
        """
        raise NotImplementedError("Subclass must implement abstract method")

    @abc.abstractmethod
    def run(self):
        """
        This method executes the specific benchmark on the VNF already
        instantiated
        :return: list of dictionaries (every dictionary contains the results
        of a data point
        """
        raise NotImplementedError("Subclass must implement abstract method")
