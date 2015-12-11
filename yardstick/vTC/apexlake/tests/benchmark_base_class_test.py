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
from experimental_framework.benchmarks import benchmark_base_class as base


class DummyBechmarkBaseClass(base.BenchmarkBaseClass):

    def get_features(self):
        features = dict()
        features['description'] = '***'
        features['parameters'] = ['A', 'B']
        features['allowed_values'] = dict()
        features['allowed_values']['A'] = ['a']
        features['allowed_values']['B'] = ['b']
        features['default_values'] = dict()
        features['default_values']['A'] = 'a'
        features['default_values']['B'] = 'b'
        return features


class TestBenchmarkBaseClass(unittest.TestCase):

    def setUp(self):
        self.mut = base.BenchmarkBaseClass('name', dict())

    def test_constructor_for_success(self):
        name = 'name'
        params = dict()
        params['A'] = 'a'
        params['B'] = 'b'
        params['C'] = 'c'
        bench_base = DummyBechmarkBaseClass(name, params)
        self.assertEqual(name, bench_base.name)
        self.assertIn('A', bench_base.params.keys())
        self.assertIn('B', bench_base.params.keys())
        self.assertEqual('a', bench_base.params['A'])
        self.assertEqual('b', bench_base.params['B'])

        params = dict()
        params['A'] = 'a'
        # params['B'] = 'b'
        bench_base = DummyBechmarkBaseClass(name, params)
        # self.assertEqual(name, bench_base.name)
        # self.assertIn('A', bench_base.params.keys())
        # self.assertIn('B', bench_base.params.keys())
        # self.assertEqual('a', bench_base.params['A'])
        # self.assertEqual('b', bench_base.params['B'])

    def test_constructor_for_failure(self):
        name = 'name'
        params = 'params'
        self.assertRaises(ValueError, DummyBechmarkBaseClass, name, params)

    def test_constructor_for_failure_2(self):
        name = 'name'
        params = dict()
        params['A'] = 'a'
        params['B'] = '*'
        self.assertRaises(ValueError, DummyBechmarkBaseClass, name, params)

    def test_init_for_failure(self):
        self.assertRaises(NotImplementedError, self.mut.init)

    def test_finalize_for_failure(self):
        self.assertRaises(NotImplementedError, self.mut.finalize)

    def test_run_for_failure(self):
        self.assertRaises(NotImplementedError, self.mut.run)

    def test_get_name_for_success(self):
        self.assertEqual(self.mut.get_name(), 'name')

