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
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxTestDataTuple
    from yardstick.network_services.traffic_profile.prox_binsearch import ProxBinSearchProfile


class TestProxBinSearchProfile(unittest.TestCase):

    def test_execute_1(self):
        def target(*args, **kwargs):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 75.0:
                return fail_tuple
            return success_tuple

        tp_config = {
            'traffic_profile': {
                'packet_sizes': [200],
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_generator = mock.MagicMock()
        traffic_generator.resource_helper.run_test = target

        profile = ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())

        profile.execute(traffic_generator)
        self.assertEqual(round(profile.current_lower, 2), 74.69)
        self.assertEqual(round(profile.current_upper, 2), 75.39)
        self.assertEqual(len(runs), 8)

    def test_execute_2(self):
        def target(*args, **kwargs):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 25.0:
                return fail_tuple
            return success_tuple

        tp_config = {
            'traffic_profile': {
                'packet_sizes': [200],
                'test_precision': 2.0,
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_generator = mock.MagicMock()
        traffic_generator.resource_helper.run_test = target

        profile = ProxBinSearchProfile(tp_config)
        profile.init(mock.MagicMock())

        profile.execute(traffic_generator)
        self.assertEqual(round(profile.current_lower, 2), 24.06)
        self.assertEqual(round(profile.current_upper, 2), 25.47)
        self.assertEqual(len(runs), 7)
