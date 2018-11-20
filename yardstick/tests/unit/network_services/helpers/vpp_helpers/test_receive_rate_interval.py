# Copyright (c) 2019 Viosoft Corporation
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

from yardstick.network_services.helpers.vpp_helpers.receive_rate_interval import \
    ReceiveRateInterval
from yardstick.network_services.helpers.vpp_helpers.receive_rate_measurement import \
    ReceiveRateMeasurement


class TestReceiveRateInterval(unittest.TestCase):

    def test__init__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertIsInstance(receive_rate_interval.measured_low,
                              ReceiveRateMeasurement)
        self.assertIsInstance(receive_rate_interval.measured_high,
                              ReceiveRateMeasurement)

    def test__init__measured_low_error(self):
        measured_low = mock.MagicMock()
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        with self.assertRaises(TypeError) as raised:
            ReceiveRateInterval(measured_low, measured_high)
        self.assertIn('measured_low is not a ReceiveRateMeasurement: ',
                      str(raised.exception))

    def test__init__measured_high_error(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = mock.MagicMock()
        with self.assertRaises(TypeError) as raised:
            ReceiveRateInterval(measured_low, measured_high)
        self.assertIn('measured_high is not a ReceiveRateMeasurement: ',
                      str(raised.exception))

    def test_sort(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertIsNone(receive_rate_interval.sort())
        self.assertEqual(119982.0, receive_rate_interval.abs_tr_width)
        self.assertEqual(0.02411,
                         receive_rate_interval.rel_tr_width)

    def test_sort_swap(self):
        measured_low = ReceiveRateMeasurement(1, 14857361, 14857339, 184965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertIsNone(receive_rate_interval.sort())
        self.assertEqual(9880018.0, receive_rate_interval.abs_tr_width)
        self.assertEqual(0.66499,
                         receive_rate_interval.rel_tr_width)

    def test_width_in_goals(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual(4.86887,
                         receive_rate_interval.width_in_goals(0.005))

    def test___str__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual(
            '[d=1.0,Tr=4857361.0,Df=0.01749;d=1.0,Tr=4977343.0,Df=0.0241)',
            receive_rate_interval.__str__())

    def test___repr__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual('ReceiveRateInterval(measured_low=' \
                         'ReceiveRateMeasurement(duration=1.0,target_tr=4857361.0,' \
                         'transmit_count=4857339,loss_count=84965),measured_high=' \
                         'ReceiveRateMeasurement(duration=1.0,target_tr=4977343.0,' \
                         'transmit_count=4977320,loss_count=119959))',
                         receive_rate_interval.__repr__())
