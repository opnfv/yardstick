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
import os
import unittest
import mock

from yardstick.network_services.vnf_generic.vnf.tg_rfc2544_ixia import \
    IXIATrafficGen
from yardstick.network_services.vnf_generic.vnf import tg_rfc2544_ixia
from yardstick.network_services.traffic_profile.base import TrafficProfile

TEST_FILE_YAML = 'nsb_test_case.yaml'


class TestIXIATrafficGen(unittest.TestCase):
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

    def test___init__(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = IXIATrafficGen(vnfd)
            self.assertEqual(ixnet_traffic_gen.tc_file_name, '')

    def test_listen_traffic(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = IXIATrafficGen(vnfd)
            self.assertEqual(None, ixnet_traffic_gen.listen_traffic({}))

    def test_instantiate(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = IXIATrafficGen(vnfd)
            scenario_cfg = {'tc': "nsb_test_case",
                            'ixia_profile': "ixload.cfg"}
            ixnet_traffic_gen.get_ixobj = mock.MagicMock()
            ixnet_traffic_gen._IxiaTrafficGen = mock.MagicMock()
            ixnet_traffic_gen._IxiaTrafficGen._connect = mock.Mock()
            self.assertRaises(
                IOError,
                ixnet_traffic_gen.instantiate("tg__1", scenario_cfg, {}))

    def test_collect_kpi(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ixnet_traffic_gen = IXIATrafficGen(vnfd)
            ixnet_traffic_gen.data = {}
            ixnet_traffic_gen._queue.put({})
            restult = ixnet_traffic_gen.collect_kpi()
            self.assertEqual({}, restult)

    def test_terminate(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            ixnet_traffic_gen = IXIATrafficGen(vnfd)
            ixnet_traffic_gen._terminated = mock.MagicMock()
            ixnet_traffic_gen._terminated.value = 0
            ixnet_traffic_gen._IxiaTrafficGen = mock.MagicMock()
            ixnet_traffic_gen._IxiaTrafficGen.ix_stop_traffic = mock.Mock()
            ixnet_traffic_gen._traffic_process = mock.MagicMock()
            ixnet_traffic_gen._traffic_process.terminate = mock.Mock()
            self.assertEqual(None, ixnet_traffic_gen.terminate())

    def test_run_traffic(self):
        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vnfd["mgmt-interface"].update({"tg-config": {}})
            vnfd["mgmt-interface"]["tg-config"].update({"ixchassis":
                                                        "1.1.1.1"})
            vnfd["mgmt-interface"]["tg-config"].update({"py_bin_path":
                                                        "/root"})
            self.sut = IXIATrafficGen(vnfd)
            self.sut.connection = mock.Mock()
            self.sut.connection.run = mock.Mock()
            self.sut._traffic_runner = mock.Mock(return_value=0)
            self.sut._traffic_process = mock.MagicMock()
            self.sut._traffic_process.start = mock.Mock()
            self.sut.client_started = mock.MagicMock()
            self.sut.client_started.value = 1
            self.sut._traffic_process.is_alive = mock.Mock(return_value=0)
            result = self.sut.run_traffic(mock_traffic_profile)
            self.assertEqual(result, True)

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

#    @mock.patch("yardstick.network_services.vnf_generic.vnf.tg_rfc2544_ixia.open")
    def test_traffic_runner(self):
        mock_traffic_profile = mock.Mock(autospec=TrafficProfile)
        mock_traffic_profile.get_traffic_definition.return_value = "64"
        mock_traffic_profile.params = self.TRAFFIC_PROFILE
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vnfd["mgmt-interface"].update({"tg-config": {}})
            vnfd["mgmt-interface"]["tg-config"].update({"ixchassis":
                                                        "1.1.1.1"})
            vnfd["mgmt-interface"]["tg-config"].update({"py_bin_path":
                                                        "/root"})
            samples = {}
            for ifname in range(1):
                name = "xe{}".format(ifname)
                samples[name] = {"Rx_Rate_Kbps": 20,
                                 "Tx_Rate_Kbps": 20,
                                 "Rx_Rate_Mbps": 10,
                                 "Tx_Rate_Mbps": 10,
                                 "RxThroughput": 10,
                                 "TxThroughput": 10,
                                 "Valid_Frames_Rx": 1000,
                                 "Frames_Tx": 1000,
                                 "in_packets": 1000,
                                 "out_packets": 1000}
            samples.update({"CurrentDropPercentage": 0.0})
            last_res = [0, {"Rx_Rate_Kbps": [20, 20],
                            "Tx_Rate_Kbps": [20, 20],
                            "Rx_Rate_Mbps": [10, 10],
                            "Tx_Rate_Mbps": [10, 10],
                            "CurrentDropPercentage": [0, 0],
                            "RxThroughput": [10, 10],
                            "TxThroughput": [10, 10],
                            "Frames_Tx": [1000, 1000],
                            "in_packets": [1000, 1000],
                            "Valid_Frames_Rx": [1000, 1000],
                            "out_packets": [1000, 1000]}]

            self.sut = IXIATrafficGen(vnfd)
            self.sut.connection = mock.Mock()
            self.sut.connection.run = mock.Mock()
            self.sut._traffic_process = mock.MagicMock()
            self.sut._traffic_process.start = mock.Mock()
            self.sut.client_started = mock.MagicMock()
            self.sut.client_started.value = 1
            self.sut.tc_file_name = \
                self._get_file_abspath(TEST_FILE_YAML)
            self.sut.generate_port_pairs = \
                mock.Mock(return_value=0)
            self.sut.tg_port_pairs = [[[0], [1]]]
            self.sut.vnf_port_pairs = [[[0], [1]]]
            self.sut._IxiaTrafficGen = mock.MagicMock()
            self.sut._IxiaTrafficGen.ix_load_config = mock.MagicMock()
            self.sut._IxiaTrafficGen.ix_stop_traffic = mock.MagicMock()
            tg_rfc2544_ixia.WAIT_AFTER_CFG_LOAD = 1
            tg_rfc2544_ixia.WAIT_FOR_TRAFFIC = 1
            self.sut._IxiaTrafficGen.ix_get_statistics = \
                mock.Mock(return_value=last_res)
            mock_traffic_profile.execute = \
                mock.Mock(return_value=['Completed', samples])
            mock_traffic_profile.get_drop_percentage = \
                mock.Mock(return_value=['Completed', samples])

            result = self.sut._traffic_runner(mock_traffic_profile,
                                              self.sut._queue,
                                              self.sut.client_started,
                                              self.sut._terminated)
            self.assertEqual(result, None)
