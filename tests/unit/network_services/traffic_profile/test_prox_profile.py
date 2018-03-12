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
    from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxResourceHelper


class TestProxProfile(unittest.TestCase):

    def test_sort_vpci(self):
        traffic_generator = mock.Mock()
        interface_1 = {'virtual-interface': {'vpci': 'id1'}, 'name': 'name1'}
        interface_2 = {'virtual-interface': {'vpci': 'id2'}, 'name': 'name2'}
        interface_3 = {'virtual-interface': {'vpci': 'id3'}, 'name': 'name3'}
        interfaces = [interface_2, interface_3, interface_1]
        traffic_generator.vnfd_helper = {
            'vdu': [{'external-interface': interfaces}]}
        output = ProxProfile.sort_vpci(traffic_generator)
        self.assertEqual([interface_1, interface_2, interface_3], output)

    def test_fill_samples(self):
        samples = {}

        traffic_generator = mock.MagicMock()
        interfaces = [
            ['id1', 'name1'],
            ['id2', 'name2']
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
        with mock.patch.object(ProxProfile, 'sort_vpci', return_value=interfaces):
            ProxProfile.fill_samples(samples, traffic_generator)

        self.assertDictEqual(samples, expected)

    def test_init(self):
        tp_config = {
            'traffic_profile': {},
        }

        profile = ProxProfile(tp_config)
        queue = mock.Mock()
        profile.init(queue)
        self.assertIs(profile.queue, queue)

    def test_execute_traffic(self):
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

        setup_helper = traffic_generator.setup_helper
        setup_helper.find_in_section.return_value = None

        prox_resource_helper = ProxResourceHelper(setup_helper)
        traffic_generator.resource_helper = prox_resource_helper

        profile = ProxProfile(tp_config)

        self.assertFalse(profile.done)
        for _ in packet_sizes:
            with self.assertRaises(NotImplementedError):
                profile.execute_traffic(traffic_generator)

        self.assertIsNone(profile.execute_traffic(traffic_generator))
        self.assertTrue(profile.done)

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

        mock_logger.debug.assert_called_once()
        self.assertEqual(mock_logger.info.call_count, 10)
