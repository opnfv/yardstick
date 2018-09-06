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

import unittest

from yardstick.network_services.traffic_profile import http


class TestTrafficProfileGenericHTTP(unittest.TestCase):

    TP_CONFIG = {'traffic_profile': {'duration': 10},
                 "uplink_0": {}, "downlink_0": {}}

    def test___init__(self):
        tp_generic_http = http.TrafficProfileGenericHTTP(
            self.TP_CONFIG)
        self.assertIsNotNone(tp_generic_http)

    def test_get_links_param(self):
        tp_generic_http = http.TrafficProfileGenericHTTP(
            self.TP_CONFIG)

        links = tp_generic_http.get_links_param()
        self.assertEqual({"uplink_0": {}, "downlink_0": {}}, links)

    def test_execute(self):
        tp_generic_http = http.TrafficProfileGenericHTTP(
            self.TP_CONFIG)
        traffic_generator = {}
        self.assertIsNone(tp_generic_http.execute(traffic_generator))

    def test__send_http_request(self):
        tp_generic_http = http.TrafficProfileGenericHTTP(
            self.TP_CONFIG)
        self.assertIsNone(tp_generic_http._send_http_request(
            '10.1.1.1', '250', '/req'))
