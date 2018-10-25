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

    @mock.patch.object(sip.SipProfile, 'execute_traffic')
    def test_execute_traffic(self, mock_execute_traffic):
        mock_generator = mock.Mock()
        self.sip_profile.execute_traffic(traffic_generator=mock_generator)
        mock_execute_traffic.assert_called()
