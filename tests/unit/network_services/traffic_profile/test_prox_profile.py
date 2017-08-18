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
    from yardstick.network_services.traffic_profile.prox_profile import ProxProfile


class TestProxProfile(unittest.TestCase):

    def test_fill_samples(self):
        samples = {}
        traffic_generator = mock.MagicMock()
        traffic_generator.vpci_if_name_ascending = [
            ['id1', 'name1'],
            ['id2', 'name2'],
        ]

        traffic_generator.resource_helper.sut.port_stats.side_effect = [
            list(range(12)),
            list(range(10, 22)),
        ]

        expected = {
            'name1': {
                'in_packets': 6,
                'out_packets': 7,
            },
            'name2': {
                'in_packets': 16,
                'out_packets': 17,
            },
        }
        ProxProfile.fill_samples(samples, traffic_generator)
        self.assertDictEqual(samples, expected)

    def test_init(self):
        tp_config = {
            'traffic_profile': {},
        }

        profile = ProxProfile(tp_config)
        profile.init(234)
        self.assertEqual(profile.queue, 234)

    def test_execute(self):
        packet_sizes = [
            10,
            100,
            1000,
        ]
        tp_config = {
            'traffic_profile': {
                'packet_sizes': packet_sizes,
            },
        }

        traffic_generator = mock.MagicMock()
        profile = ProxProfile(tp_config)

        self.assertFalse(profile.done)
        for _ in packet_sizes:
            with self.assertRaises(NotImplementedError):
                profile.execute(traffic_generator)

        self.assertIsNone(profile.execute(traffic_generator))

    def test_bounds_iterator(self):
        tp_config = {
            'traffic_profile': {},
        }

        profile = ProxProfile(tp_config)
        value = 0.0
        for value in profile.bounds_iterator():
            pass

        self.assertEqual(value, 100.0)

        mock_logger = mock.MagicMock()
        for _ in profile.bounds_iterator(mock_logger):
            pass

        self.assertEqual(mock_logger.debug.call_count, 1)
        self.assertEqual(mock_logger.info.call_count, 10)
