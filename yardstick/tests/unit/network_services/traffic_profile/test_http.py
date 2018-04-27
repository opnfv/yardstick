# Copyright (c) 2016-2017 Intel Corporation
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

from yardstick.network_services.traffic_profile.base import TrafficProfile
from yardstick.network_services.traffic_profile.http import \
    TrafficProfileGenericHTTP


class TestTrafficProfileGenericHTTP(unittest.TestCase):
    def test___init__(self):
        traffic_profile_generic_htt_p = \
            TrafficProfileGenericHTTP(TrafficProfile)
        self.assertIsNotNone(traffic_profile_generic_htt_p)

    def test_execute(self):
        traffic_profile_generic_htt_p = \
            TrafficProfileGenericHTTP(TrafficProfile)
        traffic_generator = {}
        self.assertIsNone(
            traffic_profile_generic_htt_p.execute(traffic_generator))

    def test__send_http_request(self):
        traffic_profile_generic_htt_p = \
                TrafficProfileGenericHTTP(TrafficProfile)
        self.assertIsNone(traffic_profile_generic_htt_p._send_http_request(
                             "10.1.1.1", "250", "/req"))
