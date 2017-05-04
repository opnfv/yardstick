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

from __future__ import absolute_import
import unittest
import multiprocessing
import mock

from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.nfvi import resource, collectd


class TestResourceProfile(unittest.TestCase):
    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
             [{'short-name': 'VpeVnf',
               'vdu':
               [{'routing_table':
                 [{'network': '172.16.100.20',
                   'netmask': '255.255.255.0',
                   'gateway': '172.16.100.20',
                   'if': 'xe0'},
                  {'network': '172.16.40.20',
                   'netmask': '255.255.255.0',
                   'gateway': '172.16.40.20',
                   'if': 'xe1'}],
                 'description': 'VPE approximation using DPDK',
                 'name': 'vpevnf-baremetal',
                 'nd_route_tbl':
                 [{'network': '0064:ff9b:0:0:0:0:9810:6414',
                   'netmask': '112',
                   'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                   'if': 'xe0'},
                  {'network': '0064:ff9b:0:0:0:0:9810:2814',
                   'netmask': '112',
                   'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                   'if': 'xe1'}],
                 'id': 'vpevnf-baremetal',
                 'external-interface':
                 [{'virtual-interface':
                   {'dst_mac': '3c:fd:fe:9e:64:38',
                    'vpci': '0000:05:00.0',
                    'local_ip': '172.16.100.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '0',
                    'bandwidth': '10 Gbps',
                    'dst_ip': '172.16.100.20',
                    'local_mac': '3c:fd:fe:a1:2b:80'},
                   'vnfd-connection-point-ref': 'xe0',
                   'name': 'xe0'},
                  {'virtual-interface':
                   {'dst_mac': '00:1e:67:d0:60:5c',
                    'vpci': '0000:05:00.1',
                    'local_ip': '172.16.40.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '1',
                    'bandwidth': '10 Gbps',
                    'dst_ip': '172.16.40.20',
                    'local_mac': '3c:fd:fe:a1:2b:81'},
                   'vnfd-connection-point-ref': 'xe1',
                   'name': 'xe1'}]}],
               'description': 'Vpe approximation using DPDK',
               'mgmt-interface':
                   {'vdu-id': 'vpevnf-baremetal',
                    'host': '127.0.0.1',
                    'password': 'r00t',
                    'user': 'root',
                    'ip': '127.0.0.1'},
               'benchmark':
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'}]}}

    def setUp(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.from_node.return_value = ssh_mock

            self.resource_profile = \
                ResourceProfile(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0],
                                [1, 2, 3])

    def test___init__(self):
        self.assertEqual(True, self.resource_profile.enable)

    def test_check_if_sa_running(self):
        self.assertEqual(self.resource_profile.check_if_sa_running("collectd"),
                         [True, {}])

    def test_get_cpu_data(self):
        reskey = ["", "cpufreq", "cpufreq-0"]
        value = "metric:10"
        val = self.resource_profile.get_cpu_data(reskey, value)
        self.assertIsNotNone(val)

    def test_get_cpu_data_error(self):
        reskey = ["", "", ""]
        value = "metric:10"
        val = self.resource_profile.get_cpu_data(reskey, value)
        self.assertEqual(val, ['error', 'Invalid', '', ''])

    def test__start_collectd(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            resource_profile = \
                ResourceProfile(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0],
                                [1, 2, 3])
            self.assertIsNone(
                resource_profile._start_collectd(ssh_mock, "/opt/nsb_bin"))

    def test_initiate_systemagent(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            resource_profile = \
                ResourceProfile(self.VNFD['vnfd:vnfd-catalog']['vnfd'][0],
                                [1, 2, 3])
            self.assertIsNone(
                resource_profile.initiate_systemagent("/opt/nsb_bin"))

    def test_parse_collectd_result(self):
        res = self.resource_profile.parse_collectd_result({}, [0, 1, 2])
        expected_result = {'timestamp': '', 'hugepages': {},
                           'cpu': {}, 'memory': {}}
        self.assertDictEqual(res, expected_result)

    def test_run_collectd_amqp(self):
        _queue = multiprocessing.Queue()
        resource.AmqpConsumer = mock.Mock(autospec=collectd)
        self.assertIsNone(self.resource_profile.run_collectd_amqp(_queue))

    def test_start(self):
        self.assertIsNone(self.resource_profile.start())

    def test_stop(self):
        self.assertIsNone(self.resource_profile.stop())

if __name__ == '__main__':
    unittest.main()
