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

from yardstick.network_services.helpers.vpp_helpers.receive_rate_measurement import \
    ReceiveRateMeasurement


class TestReceiveRateMeasurement(unittest.TestCase):

    def test__init__(self):
        measured = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        self.assertEqual(1, measured.duration)
        self.assertEqual(4857361, measured.target_tr)
        self.assertEqual(4857339, measured.transmit_count)
        self.assertEqual(84965, measured.loss_count)
        self.assertEqual(4772374, measured.receive_count)
        self.assertEqual(4857339, measured.transmit_rate)
        self.assertEqual(84965.0, measured.loss_rate)
        self.assertEqual(4772374.0, measured.receive_rate)
        self.assertEqual(0.01749, measured.loss_fraction)

    def test___str__(self):
        measured = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        self.assertEqual('d=1.0,Tr=4857361.0,Df=0.01749',
                         measured.__str__())

    def test___repr__(self):
        measured = ReceiveRateMeasurement(1, 4857361, 4857339, 84965)
        self.assertEqual('ReceiveRateMeasurement(duration=1.0,' \
                         'target_tr=4857361.0,transmit_count=4857339,loss_count=84965)',
                         measured.__repr__())
