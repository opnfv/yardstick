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

from yardstick.network_services.helpers.vpp_helpers.ReceiveRateInterval import \
    ReceiveRateInterval
from yardstick.network_services.helpers.vpp_helpers.ReceiveRateMeasurement import \
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

    def test_sort(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertIsNone(receive_rate_interval.sort())
        self.assertEqual(119982.0, receive_rate_interval.abs_tr_width)
        self.assertEqual(0.024105632262032172,
                         receive_rate_interval.rel_tr_width)

    def test_width_in_goals(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual(4.867974983943042,
                         receive_rate_interval.width_in_goals(0.005))

    def test___str__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual(
            '[d=1.0,Tr=4857361.0,Df=0.017492087746;d=1.0,Tr=4977343.0,Df=0.0241011226925)',
            receive_rate_interval.__str__())

    def test___repr__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        receive_rate_interval = ReceiveRateInterval(measured_low,
                                                    measured_high)
        self.assertEqual(
            'ReceiveRateInterval(measured_low=ReceiveRateMeasurement(duration=1.0,target_tr=4857361.0,transmit_count=4857339,loss_count=84965),measured_high=ReceiveRateMeasurement(duration=1.0,target_tr=4977343.0,transmit_count=4977320,loss_count=119959))',
            receive_rate_interval.__repr__())
