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

# Unittest for yardstick.network_services.traffic_profile.test_base

from __future__ import absolute_import
import unittest
import mock

from yardstick.network_services.traffic_profile.base import \
    TrafficProfile, DummyProfile


class TestTrafficProfile(unittest.TestCase):
    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64}}

    def _get_res_mock(self, **kw):
        _mock = mock.MagicMock()
        for k, v in kw.items():
            setattr(_mock, k, v)
            return _mock

    def test___init__(self):
        traffic_profile = TrafficProfile(self.TRAFFIC_PROFILE)
        self.assertEqual(self.TRAFFIC_PROFILE, traffic_profile.params)

    def test_execute(self):
        traffic_profile = TrafficProfile(self.TRAFFIC_PROFILE)
        self.assertRaises(NotImplementedError, traffic_profile.execute, {})

    def test_get(self):
        traffic_profile = TrafficProfile(self.TRAFFIC_PROFILE)
        self.assertRaises(RuntimeError, traffic_profile.get,
                          self.TRAFFIC_PROFILE)


class TestDummyProfile(unittest.TestCase):
    def test_execute(self):
        dummy_profile = DummyProfile(TrafficProfile)
        self.assertIsNone(dummy_profile.execute({}))
