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
#

import unittest
import mock

from yardstick.tests import STL_MOCKS

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxTestDataTuple
    from yardstick.network_services.traffic_profile.prox_binsearch import ProxBinSearchProfile


class TestProxBinSearchProfile(unittest.TestCase):

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

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.execute_traffic(traffic_generator)
        self.assertEqual(round(profile.current_lower, 2), 74.69)
        self.assertEqual(round(profile.current_upper, 2), 76.09)
        self.assertEqual(len(runs), 7)

        # Result Samples inc theor_max
        result_tuple = {"Result_Actual_throughput": 7.5e-07,
                        "Result_theor_max_throughput": 0.00012340000000000002,
                        "Result_pktSize": 200}
        profile.queue.put.assert_called_with(result_tuple)

        success_result_tuple = {"Success_CurrentDropPackets": 0.5,
                                "Success_DropPackets": 0.5,
                                "Success_LatencyAvg": 5.3,
                                "Success_LatencyMax": 5.2,
                                "Success_LatencyMin": 5.1,
                                "Success_PktSize": 200,
                                "Success_RxThroughput": 7.5e-07,
                                "Success_Throughput": 7.5e-07,
                                "Success_TxThroughput": 0.00012340000000000002}

        calls = profile.queue.put(success_result_tuple)
        profile.queue.put.assert_has_calls(calls)

        success_result_tuple2 = {"Success_CurrentDropPackets": 0.5,
                                "Success_DropPackets": 0.5,
                                "Success_LatencyAvg": 5.3,
                                "Success_LatencyMax": 5.2,
                                "Success_LatencyMin": 5.1,
                                "Success_PktSize": 200,
                                "Success_RxThroughput": 7.5e-07,
                                "Success_Throughput": 7.5e-07,
                                "Success_TxThroughput": 123.4,
                                "Success_can_be_lost": 409600,
                                "Success_drop_total": 20480,
                                "Success_rx_total": 4075520,
                                "Success_tx_total": 4096000}

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

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = ProxBinSearchProfile(tp_config)
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

        profile = ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.upper_bound = 100.0
        profile.lower_bound = 99.0
        profile.execute_traffic(traffic_generator)


        # Result Samples
        result_tuple = {"Result_theor_max_throughput": 0, "Result_pktSize": 200}
        profile.queue.put.assert_called_with(result_tuple)

        # Check for success_ tuple (None expected)
        calls = profile.queue.put.mock_calls
        for call in calls:
            for call_detail in call[1]:
                for k in call_detail:
                    if "Success_" in k:
                        self.assertRaises(AttributeError)
