# Copyright (c) 2017 Intel Corporation
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

from __future__ import absolute_import

import unittest
import mock

from tests.unit import STL_MOCKS

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.traffic_profile.prox_ramp import ProxRampProfile
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxTestDataTuple


class TestProxRampProfile(unittest.TestCase):

    def test_run_test_with_pkt_size(self):
        tp_config = {
            'traffic_profile': {
                'lower_bound': 10.0,
                'upper_bound': 100.0,
                'step_value': 10.0,
            },
        }

        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)

        traffic_gen = mock.MagicMock()
        traffic_gen.resource_helper.run_test.return_value = success_tuple

        profile = ProxRampProfile(tp_config)
        profile.fill_samples = fill_samples = mock.MagicMock()
        profile.queue = mock.MagicMock()

        profile.run_test_with_pkt_size(traffic_gen, 128, 30)
        self.assertEqual(traffic_gen.resource_helper.run_test.call_count, 10)
        self.assertEqual(fill_samples.call_count, 10)

    def test_run_test_with_pkt_size_with_fail(self):
        tp_config = {
            'traffic_profile': {
                'lower_bound': 10.0,
                'upper_bound': 100.0,
                'step_value': 10.0,
            },
        }

        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_gen = mock.MagicMock()
        traffic_gen.resource_helper.run_test.side_effect = [
            success_tuple,
            success_tuple,
            success_tuple,
            fail_tuple,
            success_tuple,
            fail_tuple,
            fail_tuple,
            fail_tuple,
        ]

        profile = ProxRampProfile(tp_config)
        profile.fill_samples = fill_samples = mock.MagicMock()
        profile.queue = mock.MagicMock()

        profile.run_test_with_pkt_size(traffic_gen, 128, 30)
        self.assertEqual(traffic_gen.resource_helper.run_test.call_count, 4)
        self.assertEqual(fill_samples.call_count, 3)
