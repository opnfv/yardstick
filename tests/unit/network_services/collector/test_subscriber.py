#!/usr/bin/env python

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

# Unittest for yardstick.network_services.collector.subscriber

from __future__ import absolute_import
import unittest

from yardstick.network_services.collector import subscriber


class CollectorTestCase(unittest.TestCase):

    TRAFFIC_PROFILE = {}
    VNFS = {}

    def setUp(self):
        self.test_subscriber = subscriber.Collector(self.TRAFFIC_PROFILE,
                                                    self.VNFS)

    def test_successful_init(self):

        self.assertEqual(self.test_subscriber.traffic_profile, {})
        self.assertEqual(self.test_subscriber.service, {})

    def test_unsuccessful_init(self):
        pass

    def test_start(self):
        self.assertIsNone(self.test_subscriber.start())

    def test_stop(self):
        self.assertIsNone(self.test_subscriber.stop())

    def test_get_kpi(self):

        class VnfAprrox(object):
            def __init__(self):
                self.result = {}
                self.name = "vnf__1"

            def collect_kpi(self):
                self.result = {'pkt_in_up_stream': 100,
                               'pkt_drop_up_stream': 5,
                               'pkt_in_down_stream': 50,
                               'pkt_drop_down_stream': 40}
                return self.result

        vnf = VnfAprrox()
        result = self.test_subscriber.get_kpi(vnf)

        self.assertEqual(result["vnf__1"]["pkt_in_up_stream"], 100)
        self.assertEqual(result["vnf__1"]["pkt_drop_up_stream"], 5)
        self.assertEqual(result["vnf__1"]["pkt_in_down_stream"], 50)
        self.assertEqual(result["vnf__1"]["pkt_drop_down_stream"], 40)
