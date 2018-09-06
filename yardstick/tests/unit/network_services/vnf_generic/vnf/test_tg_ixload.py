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

import subprocess

import mock
import six

from yardstick import ssh
from yardstick.benchmark.contexts import base as ctx_base
from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf import tg_ixload
from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.tests.unit import base as ut_base


NAME = "tg__1"


class TestIxLoadTrafficGen(ut_base.BaseUnitTestCase):
    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
             [{'short-name': 'VpeVnf',
               'vdu':
               [{'routing_table':
                 [{'network': '152.16.100.20',
                   'netmask': '255.255.255.0',
                   'gateway': '152.16.100.20',
                   'if': 'xe0'},
                  {'network': '152.16.40.20',
                   'netmask': '255.255.255.0',
                   'gateway': '152.16.40.20',
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
                   {'dst_mac': '00:00:00:00:00:04',
                    'vld_id': 'uplink_0',
                    'vpci': '0000:05:00.0',
                    'local_ip': '152.16.100.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': 0,
                    'bandwidth': '10 Gbps',
                    'driver': "i40e",
                    'dst_ip': '152.16.100.20',
                    'local_iface_name': 'xe0',
                    'local_mac': '00:00:00:00:00:02'},
                   'vnfd-connection-point-ref': 'xe0',
                   'name': 'xe0'},
                  {'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:03',
                    'vld_id': 'downlink_0',
                    'vpci': '0000:05:00.1',
                    'local_ip': '152.16.40.19',
                    'type': 'PCI-PASSTHROUGH',
                    'driver': "i40e",
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': 1,
                    'bandwidth': '10 Gbps',
                    'dst_ip': '152.16.40.20',
                    'local_iface_name': 'xe1',
                    'local_mac': '00:00:00:00:00:01'},
                   'vnfd-connection-point-ref': 'xe1',
                   'name': 'xe1'}]}],
               'description': 'Vpe approximation using DPDK',
               'mgmt-interface':
                   {'vdu-id': 'vpevnf-baremetal',
                    'host': '1.1.1.1',
                    'password': 'r00t',
                    'user': 'root',
                    'ip': '1.1.1.1'},
               'benchmark':
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'VpeApproxVnf', 'name': 'VPEVnfSsh'}]}}

    TRAFFIC_PROFILE = {
        "schema": "isb:traffic_profile:0.1",
        "name": "fixed",
        "description": "Fixed traffic profile to run UDP traffic",
        "traffic_profile": {
            "traffic_type": "FixedTraffic",
            "frame_rate": 100,  # pps
            "flow_number": 10,
            "frame_size": 64}}

    def setUp(self):
        self._mock_call = mock.patch.object(subprocess, 'call')
        self.mock_call = self._mock_call.start()
        self._mock_open = mock.patch.object(tg_ixload, 'open')
        self.mock_open = self._mock_open.start()
        self._mock_ssh = mock.patch.object(ssh, 'SSH')
        self.mock_ssh = self._mock_ssh.start()
        ssh_obj_mock = mock.Mock(autospec=ssh.SSH)
        ssh_obj_mock.execute = mock.Mock(return_value=(0, '', ''))
        ssh_obj_mock.run = mock.Mock(return_value=(0, '', ''))
        self.mock_ssh.from_node.return_value = ssh_obj_mock
        self.addCleanup(self._stop_mock)

    def _stop_mock(self):
        self._mock_call.stop()
        self._mock_open.stop()
        self._mock_ssh.stop()

    def test___init__(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        self.assertIsNone(ixload_traffic_gen.resource_helper.data)

    def test_update_gateways(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        links = {'uplink_0': {'ip': {}},
                 'downlink_1': {'ip': {}}}

        ixload_traffic_gen.update_gateways(links)

        self.assertEqual("152.16.100.20", links["uplink_0"]["ip"]["gateway"])
        self.assertEqual("0.0.0.0", links["downlink_1"]["ip"]["gateway"])

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server',
                       return_value='mock_node')
    def test_collect_kpi(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        ixload_traffic_gen.scenario_helper.scenario_cfg = {
            'nodes': {ixload_traffic_gen.name: "mock"}
        }
        ixload_traffic_gen.data = {}
        result = ixload_traffic_gen.collect_kpi()

        expected = {
            'physical_node': 'mock_node',
            'collect_stats': {}}
        self.assertEqual(expected, result)

    def test_listen_traffic(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        self.assertIsNone(ixload_traffic_gen.listen_traffic({}))

    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch.object(utils, 'makedirs')
    @mock.patch.object(ctx_base.Context, 'get_context_from_server')
    @mock.patch.object(tg_ixload, 'shutil')
    def test_instantiate(self, mock_shutil, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        scenario_cfg = {'tc': "nsb_test_case",
                        'ixia_profile': "ixload.cfg",
                        'task_path': "/path/to/task"}
        ixload_traffic_gen.RESULTS_MOUNT = "/tmp/result"
        mock_shutil.copy = mock.Mock()
        scenario_cfg.update(
            {'options':
                 {'packetsize': 64, 'traffic_type': 4,
                  'rfc2544': {'allowed_drop_rate': '0.8 - 1'},
                  'vnf__1': {'rules': 'acl_1rule.yaml',
                             'vnf_config': {'lb_config': 'SW',
                                            'lb_count': 1,
                                            'worker_config':
                                                '1C/1T',
                                            'worker_threads': 1}}
                  }
             }
        )
        scenario_cfg.update({'nodes': {ixload_traffic_gen.name: "mock"}})
        with mock.patch.object(six.moves.builtins, 'open',
                               create=True) as mock_open:
            mock_open.return_value = mock.MagicMock()
            ixload_traffic_gen.instantiate(scenario_cfg, {})

    @mock.patch.object(tg_ixload, 'open')
    @mock.patch.object(tg_ixload, 'min')
    @mock.patch.object(tg_ixload, 'max')
    @mock.patch.object(tg_ixload, 'len')
    @mock.patch.object(tg_ixload, 'shutil')
    def test_run_traffic(self, *args):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = '64'
        mock_traffic_profile.get_links_param.return_value = {
            'uplink_0': {'ip': {}}}
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vnfd['mgmt-interface'].update({'tg-config': {}})
        vnfd['mgmt-interface']['tg-config'].update({'ixchassis': '1.1.1.1'})
        vnfd['mgmt-interface']['tg-config'].update({'py_bin_path': '/root'})
        sut = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        sut.connection = mock.Mock()
        sut._traffic_runner = mock.Mock(return_value=0)
        result = sut.run_traffic(mock_traffic_profile)
        self.assertIsNone(result)

    @mock.patch.object(tg_ixload, 'open')
    @mock.patch.object(tg_ixload, 'min')
    @mock.patch.object(tg_ixload, 'max')
    @mock.patch.object(tg_ixload, 'len')
    @mock.patch.object(tg_ixload, 'shutil')
    def test_run_traffic_csv(self, *args):
        mock_traffic_profile = mock.Mock(autospec=tp_base.TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = '64'
        mock_traffic_profile.get_links_param.return_value = {
            'uplink_0': {'ip': {}}}
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vnfd['mgmt-interface'].update({'tg-config': {}})
        vnfd['mgmt-interface']['tg-config'].update({'ixchassis': '1.1.1.1'})
        vnfd['mgmt-interface']['tg-config'].update({'py_bin_path': '/root'})
        sut = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        sut.connection = mock.Mock()
        sut._traffic_runner = mock.Mock(return_value=0)
        subprocess.call(['touch', '/tmp/1.csv'])
        sut.rel_bin_path = mock.Mock(return_value='/tmp/*.csv')
        result = sut.run_traffic(mock_traffic_profile)
        self.assertIsNone(result)

    def test_terminate(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        self.assertIsNone(ixload_traffic_gen.terminate())

    def test_parse_csv_read(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        kpi_data = {
            'HTTP Total Throughput (Kbps)': 1,
            'HTTP Simulated Users': 2,
            'HTTP Concurrent Connections': '3',
            'HTTP Connection Rate': 4.3,
            'HTTP Transaction Rate': True,
        }
        http_reader = [kpi_data]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        result = ixload_traffic_gen.resource_helper.result
        ixload_traffic_gen.resource_helper.parse_csv_read(http_reader)
        for k_left, k_right in tg_ixload.IxLoadResourceHelper.KPI_LIST.items():
            self.assertEqual(result[k_left][-1], int(kpi_data[k_right]))

    def test_parse_csv_read_value_error(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        http_reader = [{
            'HTTP Total Throughput (Kbps)': 1,
            'HTTP Simulated Users': 2,
            'HTTP Concurrent Connections': "not a number",
            'HTTP Connection Rate': 4,
            'HTTP Transaction Rate': 5,
        }]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')
        init_value = ixload_traffic_gen.resource_helper.result
        ixload_traffic_gen.resource_helper.parse_csv_read(http_reader)
        self.assertDictEqual(ixload_traffic_gen.resource_helper.result,
                             init_value)

    def test_parse_csv_read_error(self,):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        http_reader = [{
            'HTTP Total Throughput (Kbps)': 1,
            'HTTP Simulated Users': 2,
            'HTTP Concurrent Connections': 3,
            'HTTP Transaction Rate': 5,
        }]
        ixload_traffic_gen = tg_ixload.IxLoadTrafficGen(NAME, vnfd, 'task_id')

        with self.assertRaises(KeyError):
            ixload_traffic_gen.resource_helper.parse_csv_read(http_reader)
