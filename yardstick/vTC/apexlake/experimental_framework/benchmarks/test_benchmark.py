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


from experimental_framework.benchmarks import benchmark_base_class as base


class TestBenchmark(base.BenchmarkBaseClass):

    def init(self):
        pass

    def finalize(self):
        pass

    def get_features(self):
        features = dict()
        features['description'] = 'Test Benchmark'
        features['parameters'] = list()
        features['allowed_values'] = dict()
        features['default_values'] = dict()
        return features

    def run(self):
        return dict()
