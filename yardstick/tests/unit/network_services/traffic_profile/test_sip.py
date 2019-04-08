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

from yardstick.network_services.traffic_profile import sip


class TestSipProfile(unittest.TestCase):

    TRAFFIC_PROFILE = {
        "schema": "nsb:traffic_profile:0.1",
        "name": "sip",
        "description": "Traffic profile to run sip",
        "traffic_profile": {
            "traffic_type": "SipProfile",
            "frame_rate": 100,  # pps
            "duration": 10,
            "enable_latency": False}}

    def setUp(self):
        self.sip_profile = sip.SipProfile(self.TRAFFIC_PROFILE)

    def test___init__(self):
        self.assertIsNone(self.sip_profile.generator)

    def test_execute_traffic(self):
        self.sip_profile.generator = None
        mock_traffic_generator = mock.Mock()
        self.sip_profile.execute_traffic(mock_traffic_generator)
        self.assertIsNotNone(self.sip_profile.generator)

    def test_is_ended_true(self):
        self.sip_profile.generator = mock.Mock(return_value=True)
        self.assertTrue(self.sip_profile.is_ended())

    def test_is_ended_false(self):
        self.sip_profile.generator = None
        self.assertFalse(self.sip_profile.is_ended())
