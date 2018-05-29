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

import unittest
import mock

from yardstick.network_services.collector import subscriber
from yardstick import ssh


class MockVnfAprrox(object):

    def __init__(self):
        self.result = {}
        self.name = "vnf__1"

    def collect_kpi(self):
        self.result = {
            'pkt_in_up_stream': 100,
            'pkt_drop_up_stream': 5,
            'pkt_in_down_stream': 50,
            'pkt_drop_down_stream': 40
        }
        return self.result


class CollectorTestCase(unittest.TestCase):

    NODES = {'context1': [{'name': 'node1',
                           'ip': '1.2.3.4',
                           'collectd': {
                               'plugins': {'abc': 12, 'def': 34},
                               'interval': 987
                           },
                           }]
             }

    def setUp(self):
        vnf = MockVnfAprrox()
        vnf.start_collect = mock.Mock()
        vnf.stop_collect = mock.Mock()
        self.ssh_patch = mock.patch.object(ssh, 'AutoConnectSSH')
        mock_ssh = self.ssh_patch.start()
        mock_instance = mock.Mock()
        mock_instance.execute.return_value = 0, '', ''
        mock_ssh.from_node.return_value = mock_instance
        self.collector = subscriber.Collector([vnf], self.NODES)

    def tearDown(self):
        self.ssh_patch.stop()

    def test___init__(self, *_):
        vnf = MockVnfAprrox()
        collector = subscriber.Collector([vnf], self.NODES)
        self.assertEqual(len(collector.vnfs), 1)
        self.assertEqual(len(collector.nodes), 1)

    def test_start(self, *_):
        resource_profile = mock.MagicMock()
        self.collector.resource_profiles = {'key': resource_profile}
        self.collector.bin_path = 'path'

        self.assertIsNone(self.collector.start())
        for vnf in self.collector.vnfs:
            vnf.start_collect.assert_called_once()

        for resource_profile in self.collector.resource_profiles.values():
            resource_profile.initiate_systemagent.assert_called_once_with('path')
            resource_profile.start.assert_called_once()
            resource_profile.amqp_process_for_nfvi_kpi.assert_called_once()

    def test_stop(self, *_):
        resource_profile = mock.MagicMock()
        self.collector.resource_profiles = {'key': resource_profile}

        self.assertIsNone(self.collector.stop())
        for vnf in self.collector.vnfs:
            vnf.stop_collect.assert_called_once()

        for resource in self.collector.resource_profiles.values():
            resource.stop.assert_called_once()

    def test_get_kpi(self, *_):
        result = self.collector.get_kpi()

        self.assertEqual(2, len(result))
        self.assertEqual(4, len(result["vnf__1"]))
        self.assertEqual(result["vnf__1"]["pkt_in_up_stream"], 100)
        self.assertEqual(result["vnf__1"]["pkt_drop_up_stream"], 5)
        self.assertEqual(result["vnf__1"]["pkt_in_down_stream"], 50)
        self.assertEqual(result["vnf__1"]["pkt_drop_down_stream"], 40)
