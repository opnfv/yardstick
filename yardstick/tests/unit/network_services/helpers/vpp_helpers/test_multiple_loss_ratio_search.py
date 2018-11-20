# Copyright (c) 2018 Viosoft Corporation
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

from yardstick.network_services.helpers.vpp_helpers.multiple_loss_ratio_search import \
    MultipleLossRatioSearch
from yardstick.network_services.helpers.vpp_helpers.ndr_pdr_result import \
    NdrPdrResult
from yardstick.network_services.helpers.vpp_helpers.receive_rate_interval import \
    ReceiveRateInterval
from yardstick.network_services.helpers.vpp_helpers.receive_rate_measurement import \
    ReceiveRateMeasurement
from yardstick.network_services.traffic_profile.rfc2544 import PortPgIDMap


class TestMultipleLossRatioSearch(unittest.TestCase):

    def test___init__(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(True, algorithm.latency)
        self.assertEqual(64, algorithm.pkt_size)
        self.assertEqual(30, algorithm.final_trial_duration)
        self.assertEqual(0.005, algorithm.final_relative_width)
        self.assertEqual(2, algorithm.number_of_intermediate_phases)
        self.assertEqual(1, algorithm.initial_trial_duration)
        self.assertEqual(720, algorithm.timeout)
        self.assertEqual(1, algorithm.doublings)

    def test_double_relative_width(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(0.00997, algorithm.double_relative_width(0.005))

    def test_double_step_down(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(99003.0, algorithm.double_step_down(0.005, 100000))

    def test_expand_down(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(99003.0, algorithm.expand_down(0.005, 1, 100000))

    def test_double_step_up(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(101007.0401907013,
                         algorithm.double_step_up(0.005, 100000))

    def test_expand_up(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(101007.0401907013,
                         algorithm.expand_up(0.005, 1, 100000))

    def test_half_relative_width(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(0.0025031328369998773,
                         algorithm.half_relative_width(0.005))

    def test_half_step_up(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        self.assertEqual(100250.94142341711,
                         algorithm.half_step_up(0.005, 100000))

    def test_init_generator(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(),
                                     mock.Mock(), mock.Mock()))
        self.assertEqual(ports, algorithm.ports)
        self.assertEqual(port_pg_id, algorithm.port_pg_id)

    def test_collect_kpi(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        algorithm.init_generator(ports, port_pg_id, mock.Mock, mock.Mock,
                                 mock.Mock())
        self.assertIsNone(algorithm.collect_kpi({}, 100000))

    def test_narrow_down_ndr_and_pdr(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, 'ndrpdr') as \
                        mock_ndrpdr:
            ndr_measured_low = ReceiveRateMeasurement(10, 13880000, 13879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(10, 14880000, 14879927,
                                                       0)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(10, 11880000, 11879927,
                                                      0)
            pdr_measured_high = ReceiveRateMeasurement(10, 12880000, 12879927,
                                                       0)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock_ndrpdr.return_value = MultipleLossRatioSearch.ProgressState(
                starting_result, 2, 30, 0.005, 0.0,
                4857361, 4977343)
            self.assertEqual(
                {'Result_NDR_LOWER': {'bandwidth_total_Gbps': 0.9327310944,
                                      'rate_total_pps': 1387992.7},
                 'Result_NDR_UPPER': {
                     'bandwidth_total_Gbps': 0.9999310943999999,
                     'rate_total_pps': 1487992.7},
                 'Result_NDR_packets_lost': {'packet_loss_ratio': 0.0,
                                             'packets_lost': 0.0},
                 'Result_PDR_LOWER': {
                     'bandwidth_total_Gbps': 0.7983310943999999,
                     'rate_total_pps': 1187992.7},
                 'Result_PDR_UPPER': {'bandwidth_total_Gbps': 0.8655310944,
                                      'rate_total_pps': 1287992.7},
                 'Result_PDR_packets_lost': {'packet_loss_ratio': 0.0,
                                             'packets_lost': 0.0},
                 'Result_stream0_NDR_LOWER': {'avg_latency': 3081.0,
                                              'max_latency': 3962.0,
                                              'min_latency': 1000.0},
                 'Result_stream0_PDR_LOWER': {'avg_latency': 3081.0,
                                              'max_latency': 3962.0,
                                              'min_latency': 1000.0},
                 'Result_stream1_NDR_LOWER': {'avg_latency': 3149.0,
                                              'max_latency': 3730.0,
                                              'min_latency': 500.0},
                 'Result_stream1_PDR_LOWER': {'avg_latency': 3149.0,
                                              'max_latency': 3730.0,
                                              'min_latency': 500.0}},
                algorithm.narrow_down_ndr_and_pdr(12880000, 15880000, 0.0))

    def test__measure_and_update_state(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        starting_interval = ReceiveRateInterval(measured_low, measured_high)
        starting_result = NdrPdrResult(starting_interval, starting_interval)
        previous_state = MultipleLossRatioSearch.ProgressState(starting_result,
                                                               2, 30, 0.005,
                                                               0.0, 4857361,
                                                               4977343)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure:
            mock_measure.return_value = ReceiveRateMeasurement(1,
                                                               4626121.09635,
                                                               4626100, 13074)
            state = algorithm._measure_and_update_state(previous_state,
                                                        4626121.09635)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(1, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(4626121.09635,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(4626100,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(13074,
                         state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(4613026,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(4626100,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(13074.0,
                         state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(4613026.0,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.00283,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(1, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(4857361,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(4857339,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(84965,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(4772374,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(4857339,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(84965.0,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(4772374.0,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.01749,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(1, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(4626121.09635,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(4626100,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(13074,
                         state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(4613026,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(4626100,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(13074.0,
                         state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(4613026.0,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.00283,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(1, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(4857361,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(4857339,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(84965,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(4772374,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(4857339,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(84965.0,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(4772374.0,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.01749,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(2, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.005, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(4857361, state.minimum_transmit_rate)
        self.assertEqual(4977343, state.maximum_transmit_rate)

    def test_new_interval(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 3972540.4108, 21758482, 0)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.0)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(3972540.4108, result.measured_low.target_tr)
        self.assertEqual(21758482, result.measured_low.transmit_count)
        self.assertEqual(0, result.measured_low.loss_count)
        self.assertEqual(21758482, result.measured_low.receive_count)
        self.assertEqual(21758482, result.measured_low.transmit_rate)
        self.assertEqual(0.0, result.measured_low.loss_rate)
        self.assertEqual(21758482.0, result.measured_low.receive_rate)
        self.assertEqual(0.0, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4857361, result.measured_high.target_tr)
        self.assertEqual(4857339, result.measured_high.transmit_count)
        self.assertEqual(84965, result.measured_high.loss_count)
        self.assertEqual(4772374, result.measured_high.receive_count)
        self.assertEqual(4857339, result.measured_high.transmit_rate)
        self.assertEqual(84965.0, result.measured_high.loss_rate)
        self.assertEqual(4772374.0, result.measured_high.receive_rate)
        self.assertEqual(0.01749, result.measured_high.loss_fraction)

    def test_new_interval_zero(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 4977343, 21758482, 0)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.0)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4857361.0, result.measured_low.target_tr)
        self.assertEqual(4857339, result.measured_low.transmit_count)
        self.assertEqual(84965, result.measured_low.loss_count)
        self.assertEqual(4772374, result.measured_low.receive_count)
        self.assertEqual(4857339.0, result.measured_low.transmit_rate)
        self.assertEqual(84965.0, result.measured_low.loss_rate)
        self.assertEqual(4772374.0, result.measured_low.receive_rate)
        self.assertEqual(0.01749, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4977343.0, result.measured_high.target_tr)
        self.assertEqual(21758482, result.measured_high.transmit_count)
        self.assertEqual(0, result.measured_high.loss_count)
        self.assertEqual(21758482, result.measured_high.receive_count)
        self.assertEqual(21758482.0, result.measured_high.transmit_rate)
        self.assertEqual(0.0, result.measured_high.loss_rate)
        self.assertEqual(21758482.0, result.measured_high.receive_rate)
        self.assertEqual(0.0, result.measured_high.loss_fraction)

    def test_new_interval_one(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 5000000, 2175848, 0)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.0)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4857361.0, result.measured_low.target_tr)
        self.assertEqual(4857339, result.measured_low.transmit_count)
        self.assertEqual(84965, result.measured_low.loss_count)
        self.assertEqual(4772374, result.measured_low.receive_count)
        self.assertEqual(4857339.0, result.measured_low.transmit_rate)
        self.assertEqual(84965.0, result.measured_low.loss_rate)
        self.assertEqual(4772374.0, result.measured_low.receive_rate)
        self.assertEqual(0.01749, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4977343.0, result.measured_high.target_tr)
        self.assertEqual(4977320, result.measured_high.transmit_count)
        self.assertEqual(119959, result.measured_high.loss_count)
        self.assertEqual(4857361, result.measured_high.receive_count)
        self.assertEqual(4977320.0, result.measured_high.transmit_rate)
        self.assertEqual(119959.0, result.measured_high.loss_rate)
        self.assertEqual(4857361.0, result.measured_high.receive_rate)
        self.assertEqual(0.0241, result.measured_high.loss_fraction)

    def test_new_interval_valid_1st(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 4000000, 2175848, 0)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.5)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4857361.0, result.measured_low.target_tr)
        self.assertEqual(4857339, result.measured_low.transmit_count)
        self.assertEqual(84965, result.measured_low.loss_count)
        self.assertEqual(4772374, result.measured_low.receive_count)
        self.assertEqual(4857339.0, result.measured_low.transmit_rate)
        self.assertEqual(84965.0, result.measured_low.loss_rate)
        self.assertEqual(4772374.0, result.measured_low.receive_rate)
        self.assertEqual(0.01749, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4977343.0, result.measured_high.target_tr)
        self.assertEqual(4977320, result.measured_high.transmit_count)
        self.assertEqual(119959, result.measured_high.loss_count)
        self.assertEqual(4857361, result.measured_high.receive_count)
        self.assertEqual(4977320.0, result.measured_high.transmit_rate)
        self.assertEqual(119959.0, result.measured_high.loss_rate)
        self.assertEqual(4857361.0, result.measured_high.receive_rate)
        self.assertEqual(0.0241, result.measured_high.loss_fraction)

    def test_new_interval_valid_1st_loss(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 4000000, 2175848, 1000000)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.02)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4000000.0, result.measured_low.target_tr)
        self.assertEqual(2175848, result.measured_low.transmit_count)
        self.assertEqual(1000000, result.measured_low.loss_count)
        self.assertEqual(1175848, result.measured_low.receive_count)
        self.assertEqual(2175848.0, result.measured_low.transmit_rate)
        self.assertEqual(1000000.0, result.measured_low.loss_rate)
        self.assertEqual(1175848.0, result.measured_low.receive_rate)
        self.assertEqual(0.45959, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4977343.0, result.measured_high.target_tr)
        self.assertEqual(4977320, result.measured_high.transmit_count)
        self.assertEqual(119959, result.measured_high.loss_count)
        self.assertEqual(4857361, result.measured_high.receive_count)
        self.assertEqual(4977320.0, result.measured_high.transmit_rate)
        self.assertEqual(119959.0, result.measured_high.loss_rate)
        self.assertEqual(4857361.0, result.measured_high.receive_rate)
        self.assertEqual(0.0241, result.measured_high.loss_fraction)

    def test_new_interval_valid_2nd(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 5000000, 2175848, 0)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.5)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4977343.0, result.measured_low.target_tr)
        self.assertEqual(4977320, result.measured_low.transmit_count)
        self.assertEqual(119959, result.measured_low.loss_count)
        self.assertEqual(4857361, result.measured_low.receive_count)
        self.assertEqual(4977320.0, result.measured_low.transmit_rate)
        self.assertEqual(119959.0, result.measured_low.loss_rate)
        self.assertEqual(4857361.0, result.measured_low.receive_rate)
        self.assertEqual(0.0241, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(5000000.0, result.measured_high.target_tr)
        self.assertEqual(2175848, result.measured_high.transmit_count)
        self.assertEqual(0, result.measured_high.loss_count)
        self.assertEqual(2175848, result.measured_high.receive_count)
        self.assertEqual(2175848.0, result.measured_high.transmit_rate)
        self.assertEqual(0.0, result.measured_high.loss_rate)
        self.assertEqual(2175848.0, result.measured_high.receive_rate)
        self.assertEqual(0.0, result.measured_high.loss_fraction)

    def test_new_interval_valid_3rd(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 4867361, 2175848, 0)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.5)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4867361.0, result.measured_low.target_tr)
        self.assertEqual(2175848, result.measured_low.transmit_count)
        self.assertEqual(0, result.measured_low.loss_count)
        self.assertEqual(2175848, result.measured_low.receive_count)
        self.assertEqual(2175848.0, result.measured_low.transmit_rate)
        self.assertEqual(0.0, result.measured_low.loss_rate)
        self.assertEqual(2175848.0, result.measured_low.receive_rate)
        self.assertEqual(0.0, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4977343.0, result.measured_high.target_tr)
        self.assertEqual(4977320, result.measured_high.transmit_count)
        self.assertEqual(119959, result.measured_high.loss_count)
        self.assertEqual(4857361, result.measured_high.receive_count)
        self.assertEqual(4977320.0, result.measured_high.transmit_rate)
        self.assertEqual(119959.0, result.measured_high.loss_rate)
        self.assertEqual(4857361.0, result.measured_high.receive_rate)
        self.assertEqual(0.0241, result.measured_high.loss_fraction)

    def test_new_interval_valid_3rd_loss(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        measured = ReceiveRateMeasurement(1, 4867361, 2175848, 1000000)
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        result = algorithm._new_interval(receive_rate_interval, measured, 0.2)
        self.assertIsInstance(result, ReceiveRateInterval)
        self.assertEqual(1, result.measured_low.duration)
        self.assertEqual(4857361.0, result.measured_low.target_tr)
        self.assertEqual(4857339, result.measured_low.transmit_count)
        self.assertEqual(84965, result.measured_low.loss_count)
        self.assertEqual(4772374, result.measured_low.receive_count)
        self.assertEqual(4857339.0, result.measured_low.transmit_rate)
        self.assertEqual(84965.0, result.measured_low.loss_rate)
        self.assertEqual(4772374.0, result.measured_low.receive_rate)
        self.assertEqual(0.01749, result.measured_low.loss_fraction)
        self.assertEqual(1, result.measured_high.duration)
        self.assertEqual(4867361.0, result.measured_high.target_tr)
        self.assertEqual(2175848, result.measured_high.transmit_count)
        self.assertEqual(1000000, result.measured_high.loss_count)
        self.assertEqual(1175848, result.measured_high.receive_count)
        self.assertEqual(2175848.0, result.measured_high.transmit_rate)
        self.assertEqual(1000000.0, result.measured_high.loss_rate)
        self.assertEqual(1175848.0, result.measured_high.receive_rate)
        self.assertEqual(0.45959, result.measured_high.loss_fraction)

    def test_ndrpdr(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure:
            measured_low = ReceiveRateMeasurement(30, 14880000, 14879927, 0)
            measured_high = ReceiveRateMeasurement(30, 14880000, 14879927, 0)
            measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            starting_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
            starting_result = NdrPdrResult(starting_interval,
                                           starting_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.005, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_ndr_rel_width(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            measured_low = ReceiveRateMeasurement(30, 880000, 879927, 0)
            measured_high = ReceiveRateMeasurement(30, 14880000, 14879927, 0)
            measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            starting_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
            ending_interval = ReceiveRateInterval(measured_high, measured_high)
            starting_result = NdrPdrResult(starting_interval,
                                           starting_interval)
            ending_result = NdrPdrResult(ending_interval, ending_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.005, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.005, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_pdr_rel_width(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       0)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 880000, 879927, 0)
            pdr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       0)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(ndr_interval, ndr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.005, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.005, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_ndr_lo_duration(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            measured_low = ReceiveRateMeasurement(30, 14880000, 14879927, 0)
            measured_high = ReceiveRateMeasurement(30, 14880000, 14879927, 100)
            measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            starting_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
            starting_result = NdrPdrResult(starting_interval,
                                           starting_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(starting_result, -1, 30,
                                                      0.005, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 50, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879827,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495994.23333,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(1e-05,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879827,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495994.23333,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(1e-05,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.005, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_ndr_hi_duration(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            measured_low = ReceiveRateMeasurement(60, 14880000, 14879927, 0)
            measured_high = ReceiveRateMeasurement(30, 14880000, 14879927, 100)
            measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            starting_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
            starting_result = NdrPdrResult(starting_interval,
                                           starting_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(starting_result, -1, 30,
                                                      0.005, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 50, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(60.0, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(247998.78333,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(247998.78333,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879827,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495994.23333,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(1e-05,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(60.0, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(247998.78333,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(247998.78333,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879827,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495994.23333,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(1e-05,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.005, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_error(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=0)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure:
            measured_low = ReceiveRateMeasurement(30, 14880000, 14879927, 0)
            measured_high = ReceiveRateMeasurement(30, 14880000, 14879927, 0)
            measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            starting_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
            starting_result = NdrPdrResult(starting_interval,
                                           starting_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 14880000,
                14880000)
        with self.assertRaises(RuntimeError) as raised:
            algorithm.ndrpdr(previous_state)

        self.assertIn('Optimized search takes too long.',
                      str(raised.exception))

    def test_ndrpdr_update_state_ndr_hi(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       0)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      0)
            pdr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       0)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(pdr_interval, pdr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_update_state_ndr_hi_duration(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       0)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      0)
            pdr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       0)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(pdr_interval, pdr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 50, 0.005, 0.0, 4880000,
                10880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0, state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(0, state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_update_state_ndr_lo(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      100000)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       100000)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      100000)
            pdr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       100000)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(pdr_interval, pdr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 100000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(12779927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.00776,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14779927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(492664.23333,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.00672,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(12779927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.00776,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14779927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(492664.23333,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.00672,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_update_state_pdr_lo(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       0)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      100000)
            pdr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       100000)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(pdr_interval, pdr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 100000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(12779927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.00776,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14779927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(492664.23333,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.00672,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(12779927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.00776,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14779927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(492664.23333,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.00672,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_update_state_pdr_lo_duration(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       0)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      100000)
            pdr_measured_high = ReceiveRateMeasurement(30, 14880000, 14879927,
                                                       100000)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(pdr_interval, pdr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 50, 0.005, 0.0, 14880000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(12779927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.00776,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(14880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(14779927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(492664.23333,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.00672,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(12880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(12779927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.00776,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(14880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(14879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(14779927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(495997.56667,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(492664.23333,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.00672,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_update_state_pdr_hi(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       100000)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      0)
            pdr_measured_high = ReceiveRateMeasurement(30, 13880000, 14879927,
                                                       0)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(ndr_interval, ndr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 30, 0.005, 0.0, 100000,
                14880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(10880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(10879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0,
                         state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(10879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(362664.23333,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(362664.23333,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(12779927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.00776,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(10880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(10879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0,
                         state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(10879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(362664.23333,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(362664.23333,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(12880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(12779927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.00776,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_ndrpdr_update_state_pdr_hi_duration(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock(), mock.Mock,
                                     mock.Mock()))
        with mock.patch.object(algorithm, 'measure') as \
                mock_measure, \
                mock.patch.object(algorithm, '_measure_and_update_state') as \
                        mock__measure_and_update_state:
            ndr_measured_low = ReceiveRateMeasurement(30, 10880000, 10879927,
                                                      0)
            ndr_measured_high = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                       100000)
            ndr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_low = ReceiveRateMeasurement(30, 12880000, 12879927,
                                                      0)
            pdr_measured_high = ReceiveRateMeasurement(30, 13880000, 14879927,
                                                       0)
            pdr_measured_low.latency = ['1000/3081/3962', '500/3149/3730']
            pdr_measured_high.latency = ['1000/3081/3962', '500/3149/3730']
            ndr_interval = ReceiveRateInterval(ndr_measured_low,
                                               ndr_measured_high)
            pdr_interval = ReceiveRateInterval(pdr_measured_low,
                                               pdr_measured_high)
            starting_result = NdrPdrResult(ndr_interval, pdr_interval)
            ending_result = NdrPdrResult(ndr_interval, ndr_interval)
            mock_measure.return_value = ReceiveRateMeasurement(1, 14880000,
                                                               14879927, 0)
            mock__measure_and_update_state.return_value = \
                MultipleLossRatioSearch.ProgressState(ending_result, -1, 30,
                                                      0.2, 0.0, 14880000,
                                                      14880000)
            previous_state = MultipleLossRatioSearch.ProgressState(
                starting_result, -1, 50, 0.005, 0.0, 100000,
                10880000)
            state = algorithm.ndrpdr(previous_state)
            self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertIsInstance(state, MultipleLossRatioSearch.ProgressState)
        self.assertEqual(30, state.result.ndr_interval.measured_low.duration)
        self.assertEqual(10880000.0,
                         state.result.ndr_interval.measured_low.target_tr)
        self.assertEqual(10879927,
                         state.result.ndr_interval.measured_low.transmit_count)
        self.assertEqual(0,
                         state.result.ndr_interval.measured_low.loss_count)
        self.assertEqual(10879927,
                         state.result.ndr_interval.measured_low.receive_count)
        self.assertEqual(362664.23333,
                         state.result.ndr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_rate)
        self.assertEqual(362664.23333,
                         state.result.ndr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.ndr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.ndr_interval.measured_high.duration)
        self.assertEqual(12880000.0,
                         state.result.ndr_interval.measured_high.target_tr)
        self.assertEqual(12879927,
                         state.result.ndr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.ndr_interval.measured_high.loss_count)
        self.assertEqual(12779927,
                         state.result.ndr_interval.measured_high.receive_count)
        self.assertEqual(429330.9,
                         state.result.ndr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.ndr_interval.measured_high.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.ndr_interval.measured_high.receive_rate)
        self.assertEqual(0.00776,
                         state.result.ndr_interval.measured_high.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_low.duration)
        self.assertEqual(10880000.0,
                         state.result.pdr_interval.measured_low.target_tr)
        self.assertEqual(10879927,
                         state.result.pdr_interval.measured_low.transmit_count)
        self.assertEqual(0,
                         state.result.pdr_interval.measured_low.loss_count)
        self.assertEqual(10879927,
                         state.result.pdr_interval.measured_low.receive_count)
        self.assertEqual(362664.23333,
                         state.result.pdr_interval.measured_low.transmit_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_rate)
        self.assertEqual(362664.23333,
                         state.result.pdr_interval.measured_low.receive_rate)
        self.assertEqual(0.0,
                         state.result.pdr_interval.measured_low.loss_fraction)
        self.assertEqual(30, state.result.pdr_interval.measured_high.duration)
        self.assertEqual(12880000,
                         state.result.pdr_interval.measured_high.target_tr)
        self.assertEqual(12879927,
                         state.result.pdr_interval.measured_high.transmit_count)
        self.assertEqual(100000,
                         state.result.pdr_interval.measured_high.loss_count)
        self.assertEqual(12779927,
                         state.result.pdr_interval.measured_high.receive_count)
        self.assertEqual(429330.9,
                         state.result.pdr_interval.measured_high.transmit_rate)
        self.assertEqual(3333.33333,
                         state.result.pdr_interval.measured_high.loss_rate)
        self.assertEqual(425997.56667,
                         state.result.pdr_interval.measured_high.receive_rate)
        self.assertEqual(0.00776,
                         state.result.pdr_interval.measured_high.loss_fraction)
        self.assertEqual(-1, state.phases)
        self.assertEqual(30, state.duration)
        self.assertEqual(0.2, state.width_goal)
        self.assertEqual(0.0, state.packet_loss_ratio)
        self.assertEqual(14880000, state.minimum_transmit_rate)
        self.assertEqual(14880000, state.maximum_transmit_rate)

    def test_measure(self):
        measurer = mock.MagicMock()
        measurer.sent = 102563094
        measurer.loss = 30502
        algorithm = MultipleLossRatioSearch(measurer=measurer, latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.MagicMock(),
                                     mock.Mock, mock.Mock()))
        measurement = algorithm.measure(30, 3418770.3425, True)
        self.assertIsInstance(measurement, ReceiveRateMeasurement)
        self.assertEqual(30, measurement.duration)
        self.assertEqual(3418770.3425, measurement.target_tr)
        self.assertEqual(102563094, measurement.transmit_count)
        self.assertEqual(30502, measurement.loss_count)
        self.assertEqual(102532592, measurement.receive_count)
        self.assertEqual(3418769.8, measurement.transmit_rate)
        self.assertEqual(1016.73333, measurement.loss_rate)
        self.assertEqual(3417753.06667, measurement.receive_rate)
        self.assertEqual(0.0003, measurement.loss_fraction)

    def test_perform_additional_measurements_based_on_ndrpdr_result(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        ports = [0, 1]
        port_pg_id = PortPgIDMap()
        port_pg_id.add_port(0)
        port_pg_id.add_port(1)
        self.assertIsNone(
            algorithm.init_generator(ports, port_pg_id, mock.Mock, mock.Mock,
                                     mock.Mock()))
        result = mock.MagicMock()
        result.ndr_interval.measured_low.target_tr.return_result = 100000
        self.assertIsNone(
            algorithm.perform_additional_measurements_based_on_ndrpdr_result(
                result))

    def test_display_single_bound(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        result_samples = {}
        self.assertIsNone(
            algorithm.display_single_bound(result_samples, 'NDR_LOWER',
                                           4857361, 64,
                                           ['20/849/1069', '40/69/183']))
        self.assertEqual(
            {'Result_NDR_LOWER': {'bandwidth_total_Gbps': 3.264146592,
                                  'rate_total_pps': 4857361.0},
             'Result_stream0_NDR_LOWER': {'avg_latency': 849.0,
                                          'max_latency': 1069.0,
                                          'min_latency': 20.0},
             'Result_stream1_NDR_LOWER': {'avg_latency': 69.0,
                                          'max_latency': 183.0,
                                          'min_latency': 40.0}},
            result_samples)

    def test_check_ndrpdr_interval_validity(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        result_samples = {}
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 0)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 0)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual('Minimal rate loss fraction 0.0 reach target 0.0',
                         algorithm.check_ndrpdr_interval_validity(
                             result_samples, 'NDR_LOWER',
                             receive_rate_interval))
        self.assertEqual(
            {'Result_NDR_LOWER_packets_lost': {'packet_loss_ratio': 0.0,
                                               'packets_lost': 0.0}},
            result_samples)

    def test_check_ndrpdr_interval_validity_fail(self):
        algorithm = MultipleLossRatioSearch(measurer=mock.Mock(), latency=True,
                                            pkt_size=64,
                                            final_trial_duration=30,
                                            final_relative_width=0.005,
                                            number_of_intermediate_phases=2,
                                            initial_trial_duration=1,
                                            timeout=720)
        result_samples = {}
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual(
            'Minimal rate loss fraction 0.01749 does not reach target 0.005\n84965 packets lost.',
            algorithm.check_ndrpdr_interval_validity(result_samples,
                                                     'NDR_LOWER',
                                                     receive_rate_interval,
                                                     0.005))
        self.assertEqual({'Result_NDR_LOWER_packets_lost': {
            'packet_loss_ratio': 0.01749,
            'packets_lost': 84965.0}}, result_samples)
