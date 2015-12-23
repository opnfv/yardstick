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
from experimental_framework import data_manager

class TestExperiment(unittest.TestCase):
    def setUp(self):
        self.exp = data_manager.Experiment('experiment_1')

    def tearDown(self):
        pass

    def test_add_experiment_metadata(self):
        with self.assertRaises(ValueError):
            self.exp.add_experiment_metadata('metadata')

        metadata = {
            'item_1': 'value_1',
            'item_2': 'value_2',
            'item_3': 'value_3'
        }
        self.exp.add_experiment_metadata(metadata)
        self.assertDictEqual(metadata, self.exp._metadata)
        self.assertDictEqual(metadata, self.exp.get_metadata())

    def test_experiment_configuration(self):
        with self.assertRaises(ValueError):
            self.exp.add_experiment_configuration('configuration')
        configuration = {
            'item_1': 'value_1',
            'item_2': 'value_2',
            'item_3': 'value_3'
        }
        self.exp.add_experiment_configuration(configuration)
        self.assertDictEqual(configuration, self.exp._configuration)
        self.assertDictEqual(configuration, self.exp.get_configuration())

    def test_add_benchmark(self):
        with self.assertRaises(ValueError):
            self.exp.add_benchmark(1)
        self.exp.add_benchmark('benchmark_1')
        self.assertListEqual(list(), self.exp._benchmarks['benchmark_1'])

    def test_add_datapoint(self):
        with self.assertRaises(ValueError):
            self.exp.add_data_point('benchmark_1', 'datapoint')

        data_point_1 = {
            'point_1': 'value_1',
            'point_2': 'value_2',
            'point_3': 'value_3'
        }

        with self.assertRaises(ValueError):
            self.exp.add_data_point('benchmark_1', data_point_1)

        self.exp.add_benchmark('benchmark_1')
        self.exp.add_data_point('benchmark_1', data_point_1)
        self.assertListEqual([data_point_1], self.exp._benchmarks['benchmark_1'])

    def test_get_data_points(self):
        self.assertListEqual(list(), self.exp.get_data_points('benchmark_1'))
        data_point_1 = {
            'point_1': 'value_1',
            'point_2': 'value_2',
            'point_3': 'value_3'
        }
        self.exp.add_benchmark('benchmark_1')
        self.exp.add_data_point('benchmark_1', data_point_1)
        self.assertListEqual([data_point_1], self.exp.get_data_points('benchmark_1'))

    def test_get_benchmarks(self):
        self.exp.add_benchmark('benchmark_1')
        self.exp.add_benchmark('benchmark_2')
        self.exp.add_benchmark('benchmark_3')
        expected = ['benchmark_3', 'benchmark_2','benchmark_1']
        self.assertListEqual(expected, self.exp.get_benchmarks())