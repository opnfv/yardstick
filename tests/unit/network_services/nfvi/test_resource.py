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

import errno

import mock
import unittest

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
                    'dpdk_port_num': 0,
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
                    'dpdk_port_num': 1,
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
        with mock.patch("yardstick.ssh.AutoConnectSSH") as ssh:
            self.ssh_mock = mock.Mock(autospec=ssh.SSH)
            self.ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = self.ssh_mock

            mgmt = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]['mgmt-interface']
            # interfaces = \
            #    self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]['vdu'][0]['external-interface']
            port_names = \
                self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]['vdu'][0]['external-interface']
            self.resource_profile = \
                ResourceProfile(mgmt, port_names)
            self.resource_profile.connection = self.ssh_mock

    def test___init__(self):
        self.assertTrue(self.resource_profile.enable)

    def test_check_if_system_agent_running(self):
        self.assertEqual(self.resource_profile.check_if_system_agent_running("collectd"),
                         (0, ""))

    def test_check_if_system_agent_running_excetion(self):
        with mock.patch.object(self.resource_profile.connection, "execute") as mock_execute:
            mock_execute.side_effect = OSError(errno.ECONNRESET, "error")
            self.assertEqual(
                self.resource_profile.check_if_system_agent_running("collectd"),
                (1, None))

    def test_get_cpu_data(self):
        reskey = ["", "cpufreq", "cpufreq-0"]
        value = "metric:10"
        val = self.resource_profile.get_cpu_data(reskey[1], reskey[2], value)
        self.assertIsNotNone(val)

    def test_get_cpu_data_error(self):
        reskey = ["", "", ""]
        value = "metric:10"
        val = self.resource_profile.get_cpu_data(reskey[0], reskey[1], value)
        self.assertEqual(val, ('error', 'Invalid', '', ''))

    def test__start_collectd(self):
            with self.assertRaises(Exception):
                self.resource_profile._start_collectd(self.ssh_mock, "/opt/nsb_bin")

    def test__prepare_collectd_conf(self):
            self.assertIsNone(
                self.resource_profile._prepare_collectd_conf("/opt/nsb_bin"))

    def test__setup_ovs_stats(self):
        # TODO(elfoley): This method doesn't actually return anything, the side
        # effects should be checked
        self.assertIsNone(
            self.resource_profile._setup_ovs_stats(self.ssh_mock))

    def test__provide_config_file(self,):
        loadplugin = range(5)
        port_names = range(5)
        kwargs = {
            "interval": '25',
            "loadplugin": loadplugin,
            "port_names": port_names,
        }
        self.resource_profile._provide_config_file("/opt/nsb_bin", "collectd.conf", kwargs)
        self.ssh_mock.execute.assert_called_once()

    def test_initiate_systemagent(self):
        self.resource_profile._start_collectd = mock.Mock()
        self.assertIsNone(
            self.resource_profile.initiate_systemagent("/opt/nsb_bin"))

    def test_initiate_systemagent_raise(self):
        self.resource_profile._start_collectd = mock.Mock(side_effect=RuntimeError)
        with self.assertRaises(RuntimeError):
            self.resource_profile.initiate_systemagent("/opt/nsb_bin")

    def test__parse_hugepages(self):
        reskey = ["cpu", "cpuFreq"]
        value = "timestamp:12345"
        res = self.resource_profile.parse_hugepages(reskey, value)
        self.assertEqual({'cpu/cpuFreq': '12345'}, res)

    def test__parse_dpdkstat(self):
        reskey = ["dpdk0", "0"]
        value = "tx:12345"
        res = self.resource_profile.parse_dpdkstat(reskey, value)
        self.assertEqual({'dpdk0/0': '12345'}, res)

    def test__parse_virt(self):
        reskey = ["vm0", "cpu"]
        value = "load:45"
        res = self.resource_profile.parse_virt(reskey, value)
        self.assertEqual({'vm0/cpu': '45'}, res)

    def test__parse_ovs_stats(self):
        reskey = ["ovs", "stats"]
        value = "tx:45"
        res = self.resource_profile.parse_ovs_stats(reskey, value)
        self.assertEqual({'ovs/stats': '45'}, res)

    def test_parse_collectd_result(self):
        res = self.resource_profile.parse_collectd_result({})
        expected_result = {'cpu': {}, 'dpdkstat': {}, 'hugepages': {},
                           'memory': {}, 'ovs_stats': {}, 'timestamp': '',
                           'virt': {}}
        self.assertDictEqual(res, expected_result)

    def test_parse_collectd_result_cpu(self):
        metric = {"nsb_stats/cpu/0/ipc": "101"}
        self.resource_profile.get_cpu_data = mock.Mock(return_value=[1,
                                                                     "ipc",
                                                                     "1234",
                                                                     ""])
        res = self.resource_profile.parse_collectd_result(metric)
        expected_result = {'cpu': {1: {'ipc': '1234'}}, 'dpdkstat': {}, 'hugepages': {},
                           'memory': {}, 'ovs_stats': {}, 'timestamp': '',
                           'virt': {}}
        self.assertDictEqual(res, expected_result)

    def test_parse_collectd_result_memory(self):
        metric = {"nsb_stats/memory/bw": "101"}
        res = self.resource_profile.parse_collectd_result(metric)
        expected_result = {'cpu': {}, 'dpdkstat': {}, 'hugepages': {},
                           'memory': {'bw': '101'}, 'ovs_stats': {}, 'timestamp': '',
                           'virt': {}}
        self.assertDictEqual(res, expected_result)

    def test_parse_collectd_result_hugepage(self):
        # amqp returns bytes
        metric = {b"nsb_stats/hugepages/free": b"101"}
        self.resource_profile.parse_hugepages = mock.Mock(return_value={"free": "101"})
        res = self.resource_profile.parse_collectd_result(metric)
        expected_result = {'cpu': {}, 'dpdkstat': {}, 'hugepages': {'free': '101'},
                           'memory': {}, 'ovs_stats': {}, 'timestamp': '',
                           'virt': {}}
        self.assertDictEqual(res, expected_result)

    def test_parse_collectd_result_dpdk_virt_ovs(self):
        metric = {b"nsb_stats/dpdkstat/tx": b"101",
                  b"nsb_stats/ovs_stats/tx": b"101",
                  b"nsb_stats/virt/virt/memory": b"101"}
        self.resource_profile.parse_dpdkstat = \
            mock.Mock(return_value={"tx": "101"})
        self.resource_profile.parse_virt = \
            mock.Mock(return_value={"memory": "101"})
        self.resource_profile.parse_ovs_stats = \
            mock.Mock(return_value={"tx": "101"})
        res = self.resource_profile.parse_collectd_result(metric)
        expected_result = {'cpu': {}, 'dpdkstat': {'tx': '101'}, 'hugepages': {},
                           'memory': {}, 'ovs_stats': {'tx': '101'}, 'timestamp': '',
                           'virt': {'memory': '101'}}
        self.assertDictEqual(res, expected_result)

    def test_amqp_process_for_nfvi_kpi(self):
        self.resource_profile.amqp_client = \
            mock.MagicMock(side_effect=[None, mock.MagicMock()])
        self.resource_profile.run_collectd_amqp = \
            mock.Mock(return_value=0)
        res = self.resource_profile.amqp_process_for_nfvi_kpi()
        self.assertIsNone(res)

    def test_amqp_collect_nfvi_kpi(self):
        self.resource_profile.amqp_client = \
            mock.MagicMock(side_effect=[None, mock.MagicMock()])
        self.resource_profile.run_collectd_amqp = \
            mock.Mock(return_value=0)
        self.resource_profile.parse_collectd_result = mock.Mock()
        res = self.resource_profile.amqp_collect_nfvi_kpi()
        self.assertIsNotNone(res)

    def test_run_collectd_amqp(self):
        resource.AmqpConsumer = mock.Mock(autospec=collectd)
        self.assertIsNone(self.resource_profile.run_collectd_amqp())

    def test_start(self):
        self.assertIsNone(self.resource_profile.start())

    def test_stop(self):
        self.assertIsNone(self.resource_profile.stop())

    def test_stop_amqp_not_running(self):
        self.resource_profile.amqp_client = mock.MagicMock()
        # TODO(efoley): Fix this incorrect test.
        # Should check that we don't try to stop amqp when it's not running
        self.assertIsNone(self.resource_profile.stop())
