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

import unittest
import mock

from tests.unit import STL_MOCKS

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.traffic_profile.prox_ACL import ProxACLProfile
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxTestDataTuple


class TestProxACLProfile(unittest.TestCase):

    def test_run_test_with_pkt_size(self):
        def target(*args):
            runs.append(args[2])
            if args[2] < 0 or args[2] > 100:
                raise RuntimeError(' '.join([str(args), str(runs)]))
            if args[2] > 75.0:
                return fail_tuple, {}
            return success_tuple, {}

        tp_config = {
            'traffic_profile': {
                'upper_bound': 100.0,
                'lower_bound': 0.0,
                'tolerated_loss': 50.0,
                'attempts': 20
            },
        }

        runs = []
        success_tuple = ProxTestDataTuple(
            10.0, 1, 2, 3, 4, [5.1, 5.2, 5.3], 995, 1000, 123.4)
        fail_tuple = ProxTestDataTuple(
            10.0, 1, 2, 3, 4, [5.6, 5.7, 5.8], 850, 1000, 123.4)

        traffic_gen = mock.MagicMock()

        profile_helper = mock.MagicMock()
        profile_helper.run_test = target

        profile = ProxACLProfile(tp_config)
        profile.init(mock.MagicMock())

        profile.prox_config["attempts"] = 20
        profile.queue = mock.MagicMock()
        profile.tolerated_loss = 50.0
        profile.pkt_size = 128
        profile.duration = 30
        profile.test_value = 100.0
        profile.tolerated_loss = 100.0
        profile._profile_helper = profile_helper

        profile.run_test_with_pkt_size(
            traffic_gen, profile.pkt_size, profile.duration)
