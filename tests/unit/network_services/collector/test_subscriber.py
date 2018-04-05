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
import mock

from yardstick.network_services.collector import subscriber


class MockVnfAprrox(object):

    def __init__(self):
        self.result = {}
        self.name = "vnf__1"

    def start_collect(self):
        pass

    def stop_collect(self):
        pass

    def collect_kpi(self):
        self.result = {
            'pkt_in_up_stream': 100,
            'pkt_drop_up_stream': 5,
            'pkt_in_down_stream': 50,
            'pkt_drop_down_stream': 40
        }
        return self.result


class CollectorTestCase(unittest.TestCase):

    NODES = {
        'node1': {},
        'node2': {
            'ip': '1.2.3.4',
            'collectd': {
                'plugins': {'abc': 12, 'def': 34},
                'interval': 987,
            },
        },
    }
    TRAFFIC_PROFILE = {
        'key1': 'value1',
    }

    def setUp(self):
        vnf = MockVnfAprrox()
        self.ssh_patch = mock.patch('yardstick.ssh.AutoConnectSSH')
        mock_ssh = self.ssh_patch.start()
        mock_instance = mock.Mock()
        mock_instance.execute.return_value = 0, '', ''
        mock_ssh.from_node.return_value = mock_instance
        self.collector = subscriber.Collector([vnf])

    def tearDown(self):
        self.ssh_patch.stop()

    def test___init__(self, *_):
        vnf = MockVnfAprrox()
        collector = subscriber.Collector([vnf])
        self.assertEqual(len(collector.vnfs), 1)

    def test___init___with_data(self, *_):
        self.assertEqual(len(self.collector.vnfs), 1)

    def test___init___negative(self, *_):
        pass

    def test_start(self, *_):
        self.assertIsNone(self.collector.start())

    def test_stop(self, *_):
        self.assertIsNone(self.collector.stop())

    def test_get_kpi(self, *_):
        result = self.collector.get_kpi()

        self.assertEqual(result["vnf__1"]["pkt_in_up_stream"], 100)
        self.assertEqual(result["vnf__1"]["pkt_drop_up_stream"], 5)
        self.assertEqual(result["vnf__1"]["pkt_in_down_stream"], 50)
        self.assertEqual(result["vnf__1"]["pkt_drop_down_stream"], 40)
        self.assertNotIn('node2', result)
