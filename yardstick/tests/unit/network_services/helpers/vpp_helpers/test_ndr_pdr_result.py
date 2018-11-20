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

from yardstick.network_services.helpers.vpp_helpers.ndr_pdr_result import \
    NdrPdrResult
from yardstick.network_services.helpers.vpp_helpers.receive_rate_interval import \
    ReceiveRateInterval
from yardstick.network_services.helpers.vpp_helpers.receive_rate_measurement import \
    ReceiveRateMeasurement


class TestNdrPdrResult(unittest.TestCase):

    def test___init__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        starting_interval = ReceiveRateInterval(measured_low, measured_high)
        ndrpdr_result = NdrPdrResult(starting_interval, starting_interval)
        self.assertIsInstance(ndrpdr_result.ndr_interval, ReceiveRateInterval)
        self.assertIsInstance(ndrpdr_result.pdr_interval, ReceiveRateInterval)

    def test___init__ndr_error(self):
        starting_interval = mock.MagicMock()
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        end_interval = ReceiveRateInterval(measured_low, measured_high)
        with self.assertRaises(TypeError) as raised:
            NdrPdrResult(starting_interval, end_interval)
        self.assertIn('ndr_interval, is not a ReceiveRateInterval: ',
                      str(raised.exception))

    def test___init__pdr_error(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        starting_interval = ReceiveRateInterval(measured_low, measured_high)
        end_interval = mock.MagicMock()
        with self.assertRaises(TypeError) as raised:
            NdrPdrResult(starting_interval, end_interval)
        self.assertIn('pdr_interval, is not a ReceiveRateInterval: ',
                      str(raised.exception))

    def test_width_in_goals(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        starting_interval = ReceiveRateInterval(measured_low, measured_high)
        ndrpdr_result = NdrPdrResult(starting_interval, starting_interval)
        self.assertEqual('ndr 4.86887; pdr 4.86887',
                         ndrpdr_result.width_in_goals(0.005))

    def test___str__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        starting_interval = ReceiveRateInterval(measured_low, measured_high)
        ndrpdr_result = NdrPdrResult(starting_interval, starting_interval)
        self.assertEqual(
            'NDR=[d=1.0,Tr=4857361.0,Df=0.01749;d=1.0,Tr=4977343.0,Df=0.0241);'
            'PDR=[d=1.0,Tr=4857361.0,Df=0.01749;d=1.0,Tr=4977343.0,Df=0.0241)',
            ndrpdr_result.__str__())

    def test___repr__(self):
        measured_low = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        measured_high = ReceiveRateMeasurement(1, 4977343, 4977320, 119959)
        starting_interval = ReceiveRateInterval(measured_low, measured_high)
        ndrpdr_result = NdrPdrResult(starting_interval, starting_interval)
        self.assertEqual(
            'NdrPdrResult(ndr_interval=ReceiveRateInterval(measured_low=' \
            'ReceiveRateMeasurement(duration=1.0,target_tr=4857361.0,' \
            'transmit_count=4857339,loss_count=84965),measured_high=' \
            'ReceiveRateMeasurement(duration=1.0,target_tr=4977343.0,' \
            'transmit_count=4977320,loss_count=119959)),pdr_interval=' \
            'ReceiveRateInterval(measured_low=ReceiveRateMeasurement' \
            '(duration=1.0,target_tr=4857361.0,transmit_count=4857339,' \
            'loss_count=84965),measured_high=ReceiveRateMeasurement' \
            '(duration=1.0,target_tr=4977343.0,transmit_count=4977320,' \
            'loss_count=119959)))',
            ndrpdr_result.__repr__())
