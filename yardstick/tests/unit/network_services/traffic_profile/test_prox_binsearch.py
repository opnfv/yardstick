# Copyright (c) 2017 Intel Corporation
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

from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxTestDataTuple
from yardstick.network_services.traffic_profile import prox_binsearch


class TestProxBinSearchProfile(unittest.TestCase):

    def setUp(self):
        self._mock_log_info = mock.patch.object(prox_binsearch.LOG, 'info')
        self.mock_log_info = self._mock_log_info.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_log_info.stop()

    def test_execute_1(self):
        def target(*args, **_):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 75.0:
                return fail_tuple, {}
            return success_tuple, {}

        tp_config = {
            'traffic_profile': {
                'packet_sizes': [200],
                'test_precision': 2.0,
                'tolerated_loss': 0.001,
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_generator = mock.MagicMock()
        attrs1 = {'get.return_value' : 10}
        traffic_generator.scenario_helper.all_options.configure_mock(**attrs1)

        attrs2 = {'__getitem__.return_value' : 10, 'get.return_value': 10}
        traffic_generator.scenario_helper.scenario_cfg["runner"].configure_mock(**attrs2)

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = prox_binsearch.ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.execute_traffic(traffic_generator)

        self.assertEqual(round(profile.current_lower, 2), 74.69)
        self.assertEqual(round(profile.current_upper, 2), 76.09)
        self.assertEqual(len(runs), 77)

        # Result Samples inc theor_max
        result_tuple = {'Actual_throughput': 5e-07,
                        'theor_max_throughput': 7.5e-07,
                        'PktSize': 200,
                        'Status': 'Result'}

        test_results = profile.queue.put.call_args[0]
        for k in result_tuple:
            self.assertEqual(result_tuple[k], test_results[0][k])

        success_result_tuple = {"CurrentDropPackets": 0.5,
                                "DropPackets": 0.5,
                                "LatencyAvg": 5.3,
                                "LatencyMax": 5.2,
                                "LatencyMin": 5.1,
                                "PktSize": 200,
                                "RxThroughput": 7.5e-07,
                                "Throughput": 7.5e-07,
                                "TxThroughput": 0.00012340000000000002,
                                "Status": 'Success'}

        calls = profile.queue.put(success_result_tuple)
        profile.queue.put.assert_has_calls(calls)

        success_result_tuple2 = {"CurrentDropPackets": 0.5,
                                "DropPackets": 0.5,
                                "LatencyAvg": 5.3,
                                "LatencyMax": 5.2,
                                "LatencyMin": 5.1,
                                "PktSize": 200,
                                "RxThroughput": 7.5e-07,
                                "Throughput": 7.5e-07,
                                "TxThroughput": 123.4,
                                "can_be_lost": 409600,
                                "drop_total": 20480,
                                "rx_total": 4075520,
                                "tx_total": 4096000,
                                "Status": 'Success'}

        calls = profile.queue.put(success_result_tuple2)
        profile.queue.put.assert_has_calls(calls)

    def test_execute_2(self):
        def target(*args, **_):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 25.0:
                return fail_tuple, {}
            return success_tuple, {}

        tp_config = {
            'traffic_profile': {
                'packet_sizes': [200],
                'test_precision': 2.0,
                'tolerated_loss': 0.001,
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_generator = mock.MagicMock()
        attrs1 = {'get.return_value': 10}
        traffic_generator.scenario_helper.all_options.configure_mock(**attrs1)

        attrs2 = {'__getitem__.return_value': 0, 'get.return_value': 0}
        traffic_generator.scenario_helper.scenario_cfg["runner"].configure_mock(**attrs2)

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = prox_binsearch.ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.execute_traffic(traffic_generator)
        self.assertEqual(round(profile.current_lower, 2), 24.06)
        self.assertEqual(round(profile.current_upper, 2), 25.47)
        self.assertEqual(len(runs), 7)

    def test_execute_3(self):
        def target(*args, **_):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 75.0:
                return fail_tuple, {}
            return success_tuple, {}

        tp_config = {
            'traffic_profile': {
                'packet_sizes': [200],
                'test_precision': 2.0,
                'tolerated_loss': 0.001,
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_generator = mock.MagicMock()

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = prox_binsearch.ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.upper_bound = 100.0
        profile.lower_bound = 99.0
        profile.execute_traffic(traffic_generator)


        # Result Samples
        result_tuple = {'Actual_throughput': 0, 'theor_max_throughput': 0,
                        "Status": 'Result', "Next_Step": ''}
        profile.queue.put.assert_called_with(result_tuple)

        # Check for success_ tuple (None expected)
        calls = profile.queue.put.mock_calls
        for call in calls:
            for call_detail in call[1]:
                if call_detail["Status"] == 'Success':
                    self.assertRaises(AttributeError)

    def test_execute_4(self):

        def target(*args, **_):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 75.0:
                return fail_tuple, {}
            return success_tuple, {}

        tp_config = {
            'traffic_profile': {
                'packet_sizes': [200],
                'test_precision': 2.0,
                'tolerated_loss': 0.001,
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_generator = mock.MagicMock()
        attrs1 = {'get.return_value': 100000}
        traffic_generator.scenario_helper.all_options.configure_mock(**attrs1)

        attrs2 = {'__getitem__.return_value': 0, 'get.return_value': 0}
        traffic_generator.scenario_helper.scenario_cfg["runner"].configure_mock(**attrs2)

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = prox_binsearch.ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.execute_traffic(traffic_generator)
        self.assertEqual(round(profile.current_lower, 2), 74.69)
        self.assertEqual(round(profile.current_upper, 2), 76.09)
        self.assertEqual(len(runs), 7)

        # Result Samples inc theor_max
        result_tuple = {'Actual_throughput': 5e-07,
                        'theor_max_throughput': 7.5e-07,
                        'PktSize': 200,
                        "Status": 'Result'}

        test_results = profile.queue.put.call_args[0]
        for k in result_tuple:
            self.assertEqual(result_tuple[k], test_results[0][k])

        success_result_tuple = {"CurrentDropPackets": 0.5,
                                "DropPackets": 0.5,
                                "LatencyAvg": 5.3,
                                "LatencyMax": 5.2,
                                "LatencyMin": 5.1,
                                "PktSize": 200,
                                "RxThroughput": 7.5e-07,
                                "Throughput": 7.5e-07,
                                "TxThroughput": 0.00012340000000000002,
                                "Status": 'Success'}

        calls = profile.queue.put(success_result_tuple)
        profile.queue.put.assert_has_calls(calls)

        success_result_tuple2 = {"CurrentDropPackets": 0.5,
                                 "DropPackets": 0.5,
                                 "LatencyAvg": 5.3,
                                 "LatencyMax": 5.2,
                                 "LatencyMin": 5.1,
                                 "PktSize": 200,
                                 "RxThroughput": 7.5e-07,
                                 "Throughput": 7.5e-07,
                                 "TxThroughput": 123.4,
                                 "can_be_lost": 409600,
                                 "drop_total": 20480,
                                 "rx_total": 4075520,
                                 "tx_total": 4096000,
                                 "Status": 'Success'}

        calls = profile.queue.put(success_result_tuple2)
        profile.queue.put.assert_has_calls(calls)
