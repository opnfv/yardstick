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
from experimental_framework.benchmarks import rfc2544_throughput_benchmark as mut
import experimental_framework.common as common


class RFC2544ThroughputBenchmarkRunTest(unittest.TestCase):

    def setUp(self):
        name = 'benchmark'
        params = dict()
        params[mut.VLAN_SENDER] = '1'
        params[mut.VLAN_RECEIVER] = '2'
        self.benchmark = mut.RFC2544ThroughputBenchmark(name, params)
        common.init_log()

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

    def test_init(self):
        self.assertEqual(self.benchmark.init(), None)

    def test_finalize(self):
        self.assertEqual(self.benchmark.finalize(), None)

    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark.'
                '_reset_lua_file')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark.'
                '_configure_lua_file')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark.'
                '_extract_packet_size_from_params')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark.'
                '_get_results')
    @mock.patch('experimental_framework.benchmarks.'
                'rfc2544_throughput_benchmark.dpdk.DpdkPacketGenerator')
    def test_run_for_success(self, mock_dpdk, mock_get_results, 
                             mock_extract_size, conf_lua_file_mock,
                             reset_lua_file_mock):
        expected = {'results': 0, 'packet_size': '1'}
        mock_extract_size.return_value = '1'
        mock_get_results.return_value = {'results': 0}
        output = self.benchmark.run()
        self.assertEqual(expected, output)
        conf_lua_file_mock.assert_called_once()
        reset_lua_file_mock.assert_called_once()
        dpdk_instance = mock_dpdk()
        dpdk_instance.init_dpdk_pktgen.assert_called_once_with(
            dpdk_interfaces=2, pcap_file_0='packet_1.pcap',
            pcap_file_1='igmp.pcap', lua_script='rfc2544.lua',
            vlan_0='1', vlan_1='2')
        dpdk_instance.send_traffic.assert_called_once_with()


class RFC2544ThroughputBenchmarkOthers(unittest.TestCase):

    def setUp(self):
        name = 'benchmark'
        params = {'packet_size': '128'}
        self.benchmark = mut.RFC2544ThroughputBenchmark(name, params)

    def tearDown(self):
        pass

    def test__extract_packet_size_from_params_for_success(self):
        expected = '128'
        output = self.benchmark._extract_packet_size_from_params()
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.replace_in_file')
    def test__configure_lua_file(self, mock_common_replace_in_file):
        self.benchmark.lua_file = 'lua_file'
        self.benchmark.results_file = 'result_file'
        self.benchmark._configure_lua_file()
        mock_common_replace_in_file.\
            assert_called_once_with('lua_file', 'local out_file = ""',
                                    'local out_file = "result_file"')

    @mock.patch('experimental_framework.common.replace_in_file')
    def test__reset_lua_file(self, mock_common_replace_in_file):
        self.benchmark.lua_file = 'lua_file'
        self.benchmark.results_file = 'result_file'
        self.benchmark._reset_lua_file()
        mock_common_replace_in_file.\
            assert_called_once_with('lua_file',
                                    'local out_file = "result_file"',
                                    'local out_file = ""')


class RFC2544ThroughputBenchmarkGetResultsTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('experimental_framework.common.get_file_first_line')
    def test__get_results_for_success(self, mock_common_file_line):
        name = 'benchmark'
        params = {'packet_size': '128'}
        self.benchmark = mut.RFC2544ThroughputBenchmark(name, params)
        self.benchmark.results_file = 'base_dir/experimental_framework/' \
                                      'packet_generators/dpdk_pktgen/' \
                                      'experiment.res'
        mock_common_file_line.return_value = '10'
        expected = {'throughput': 10}
        output = self.benchmark._get_results()
        self.assertEqual(expected, output)
        mock_common_file_line.\
            assert_called_once_with('base_dir/experimental_framework/'
                                    'packet_generators/dpdk_pktgen/'
                                    'experiment.res')

    @mock.patch('experimental_framework.common.get_file_first_line')
    def test__get_results_for_success_2(self, mock_common_file_line):
        name = 'benchmark'
        params = {'packet_size': '128'}
        self.benchmark = mut.RFC2544ThroughputBenchmark(name, params)
        self.benchmark.results_file = 'base_dir/experimental_framework/' \
                                      'packet_generators/dpdk_pktgen/' \
                                      'experiment.res'
        mock_common_file_line.return_value = '1XXX0'
        expected = {'throughput': 0}
        output = self.benchmark._get_results()
        self.assertEqual(expected, output)
        mock_common_file_line.\
            assert_called_once_with('base_dir/experimental_framework/'
                                    'packet_generators/dpdk_pktgen/'
                                    'experiment.res')
