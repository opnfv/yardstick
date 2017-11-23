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

import sys

import mock
import unittest

from yardstick.common import exceptions
from yardstick.network_services import traffic_profile as tprofile_package
from yardstick.network_services.traffic_profile import base
from yardstick import tests as y_tests


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
        traffic_profile = base.TrafficProfile(self.TRAFFIC_PROFILE)
        self.assertEqual(self.TRAFFIC_PROFILE, traffic_profile.params)

    def test_execute(self):
        traffic_profile = base.TrafficProfile(self.TRAFFIC_PROFILE)
        self.assertRaises(NotImplementedError,
                          traffic_profile.execute_traffic, {})

    def test_get_existing_traffic_profile(self):
        traffic_profile_list = [
            'RFC2544Profile', 'FixedProfile', 'TrafficProfileGenericHTTP',
            'IXIARFC2544Profile', 'ProxACLProfile', 'ProxBinSearchProfile',
            'ProxProfile', 'ProxRampProfile']
        with mock.patch.dict(sys.modules, y_tests.STL_MOCKS):
            tprofile_package.register_modules()

            for tp in traffic_profile_list:
                traffic_profile = base.TrafficProfile.get(
                    {'traffic_profile': {'traffic_type': tp}})
                self.assertEqual(tp, traffic_profile.__class__.__name__)

    def test_get_non_existing_traffic_profile(self):
        self.assertRaises(exceptions.TrafficProfileNotImplemented,
                          base.TrafficProfile.get, self.TRAFFIC_PROFILE)


class TestDummyProfile(unittest.TestCase):
    def test_execute(self):
        dummy_profile = base.DummyProfile(base.TrafficProfile)
        self.assertIsNone(dummy_profile.execute({}))
