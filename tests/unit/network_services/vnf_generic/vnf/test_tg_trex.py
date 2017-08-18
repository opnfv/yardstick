#!/usr/bin/env python

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

from __future__ import absolute_import

import unittest
import mock

from tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh
from tests.unit import STL_MOCKS


NAME = 'vnf_1'

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.tg_trex import \
    TrexTrafficGen, TrexResourceHelper
    from yardstick.network_services.traffic_profile.base import TrafficProfile


class TestTrexTrafficGen(unittest.TestCase):
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
                    'vpci': '0000:05:00.0',
                    'local_ip': '152.16.100.19',
                    'type': 'PCI-PASSTHROUGH',
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '0',
                    'bandwidth': '10 Gbps',
                    'driver': "i40e",
                    'dst_ip': '152.16.100.20',
                    'local_iface_name': 'xe0',
                    'local_mac': '00:00:00:00:00:02'},
                   'vnfd-connection-point-ref': 'xe0',
                   'name': 'xe0'},
                  {'virtual-interface':
                   {'dst_mac': '00:00:00:00:00:03',
                    'vpci': '0000:05:00.1',
                    'local_ip': '152.16.40.19',
                    'type': 'PCI-PASSTHROUGH',
                    'driver': "i40e",
                    'netmask': '255.255.255.0',
                    'dpdk_port_num': '1',
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

    @mock.patch("yardstick.ssh.SSH")
    def test___init__(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        self.assertIsInstance(trex_traffic_gen.resource_helper, TrexResourceHelper)

    @mock.patch("yardstick.ssh.SSH")
    def test_collect_kpi(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper._queue.put({})
        result = trex_traffic_gen.collect_kpi()
        self.assertEqual({}, result)

    @mock.patch("yardstick.ssh.SSH")
    def test_listen_traffic(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        self.assertIsNone(trex_traffic_gen.listen_traffic({}))

    @mock.patch("yardstick.ssh.SSH")
    def test_instantiate(self, ssh):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen._tg_process = mock.MagicMock()
        trex_traffic_gen._tg_process.start = mock.Mock()
        trex_traffic_gen._tg_process.exitcode = 0
        trex_traffic_gen._tg_process._is_alive = mock.Mock(return_value=1)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.instantiate({}, {}))

    @mock.patch("yardstick.ssh.SSH")
    def test_instantiate_error(self, ssh):
        mock_ssh(ssh, exec_result=(1, "", ""))

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen._start_server = mock.Mock(return_value=0)
        trex_traffic_gen._tg_process = mock.MagicMock()
        trex_traffic_gen._tg_process.start = mock.Mock()
        trex_traffic_gen._tg_process._is_alive = mock.Mock(return_value=0)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.instantiate({}, {}))

    @mock.patch("yardstick.ssh.SSH")
    def test__start_server(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen._start_server())

    @mock.patch("yardstick.ssh.SSH")
    def test__traffic_runner(self, ssh):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.execute.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.sut = TrexTrafficGen(NAME, vnfd)
        self.sut.ssh_helper = mock.Mock()
        self.sut.ssh_helper.run = mock.Mock()
        self.sut._vpci_ascending = ["0000:05:00.0", "0000:05:00.1"]
        self.sut._connect_client = mock.Mock(autospec=STLClient)
        self.sut._connect_client.get_stats = mock.Mock(return_value="0")
        self.sut.resource_helper.RUN_DURATION = 0
        self.sut.resource_helper.QUEUE_WAIT_TIME = 0
        self.sut._traffic_runner(mock_traffic_profile)

    @mock.patch("yardstick.ssh.SSH")
    def test__generate_trex_cfg(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.resource_helper.generate_cfg())

    @mock.patch("yardstick.ssh.SSH")
    def test_run_traffic(self, ssh):
        mock_ssh(ssh)

        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.sut = TrexTrafficGen(NAME, vnfd)
        self.sut.ssh_helper = mock.Mock()
        self.sut.ssh_helper.run = mock.Mock()
        self.sut._traffic_runner = mock.Mock(return_value=0)
        self.sut.resource_helper.client_started.value = 1
        result = self.sut.run_traffic(mock_traffic_profile)
        self.sut._traffic_process.terminate()
        self.assertIsNotNone(result)

    @mock.patch("yardstick.ssh.SSH")
    def test_scale(self, ssh):
        mock_ssh(ssh, exec_result=(1, "", ""))
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.scale('')

    @mock.patch("yardstick.ssh.SSH")
    def test_setup_vnf_environment(self, ssh):
        mock_ssh(ssh, exec_result=(1, "", ""))
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        self.assertIsNone(trex_traffic_gen.setup_helper.setup_vnf_environment())

    @mock.patch("yardstick.ssh.SSH")
    def test_terminate(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        trex_traffic_gen.ssh_helper = mock.MagicMock()
        trex_traffic_gen.resource_helper.ssh_helper = mock.MagicMock()
        self.assertIsNone(trex_traffic_gen.terminate())

    @mock.patch("yardstick.ssh.SSH")
    def test__connect_client(self, ssh):
        mock_ssh(ssh)
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        trex_traffic_gen = TrexTrafficGen(NAME, vnfd)
        client = mock.Mock(autospec=STLClient)
        client.connect = mock.Mock(return_value=0)
        self.assertIsNotNone(trex_traffic_gen.resource_helper._connect(client))

if __name__ == '__main__':
    unittest.main()
