# Copyright (c) 2018-2019 Intel Corporation
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
import time

import unittest
import mock

from yardstick.network_services.traffic_profile import prox_irq


class TestProxIrqProfile(unittest.TestCase):

    def setUp(self):
        self._mock_log_info = mock.patch.object(prox_irq.LOG, 'info')
        self.mock_log_info = self._mock_log_info.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_log_info.stop()

    @mock.patch.object(time, 'sleep')
    def test_execute_1(self, *args):
        tp_config = {
            'traffic_profile': {
            },
        }

        traffic_generator = mock.MagicMock()
        attrs1 = {'get.return_value' : 10}
        traffic_generator.scenario_helper.all_options.configure_mock(**attrs1)

        attrs2 = {'__getitem__.return_value' : 10, 'get.return_value': 10}
        traffic_generator.scenario_helper.scenario_cfg["runner"].configure_mock(**attrs2)

        profile_helper = mock.MagicMock()

        profile = prox_irq.ProxIrqProfile(tp_config)
        profile.init(mock.MagicMock())
        profile._profile_helper = profile_helper

        profile.execute_traffic(traffic_generator)
        profile.run_test()
        is_ended_flag = profile.is_ended()

        self.assertFalse(is_ended_flag)
        self.assertEqual(profile.lower_bound, 10.0)
