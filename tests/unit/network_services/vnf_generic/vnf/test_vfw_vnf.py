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
import os

STL_MOCKS = {
    'stl': mock.MagicMock(),
    'stl.trex_stl_lib': mock.MagicMock(),
    'stl.trex_stl_lib.base64': mock.MagicMock(),
    'stl.trex_stl_lib.binascii': mock.MagicMock(),
    'stl.trex_stl_lib.collections': mock.MagicMock(),
    'stl.trex_stl_lib.copy': mock.MagicMock(),
    'stl.trex_stl_lib.datetime': mock.MagicMock(),
    'stl.trex_stl_lib.functools': mock.MagicMock(),
    'stl.trex_stl_lib.imp': mock.MagicMock(),
    'stl.trex_stl_lib.inspect': mock.MagicMock(),
    'stl.trex_stl_lib.json': mock.MagicMock(),
    'stl.trex_stl_lib.linecache': mock.MagicMock(),
    'stl.trex_stl_lib.math': mock.MagicMock(),
    'stl.trex_stl_lib.os': mock.MagicMock(),
    'stl.trex_stl_lib.platform': mock.MagicMock(),
    'stl.trex_stl_lib.pprint': mock.MagicMock(),
    'stl.trex_stl_lib.random': mock.MagicMock(),
    'stl.trex_stl_lib.re': mock.MagicMock(),
    'stl.trex_stl_lib.scapy': mock.MagicMock(),
    'stl.trex_stl_lib.socket': mock.MagicMock(),
    'stl.trex_stl_lib.string': mock.MagicMock(),
    'stl.trex_stl_lib.struct': mock.MagicMock(),
    'stl.trex_stl_lib.sys': mock.MagicMock(),
    'stl.trex_stl_lib.threading': mock.MagicMock(),
    'stl.trex_stl_lib.time': mock.MagicMock(),
    'stl.trex_stl_lib.traceback': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_async_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_exceptions': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_ext': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_jsonrpc_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_interface': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_scapy': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_port': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_stats': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_streams': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_types': mock.MagicMock(),
    'stl.trex_stl_lib.types': mock.MagicMock(),
    'stl.trex_stl_lib.utils': mock.MagicMock(),
    'stl.trex_stl_lib.utils.argparse': mock.MagicMock(),
    'stl.trex_stl_lib.utils.collections': mock.MagicMock(),
    'stl.trex_stl_lib.utils.common': mock.MagicMock(),
    'stl.trex_stl_lib.utils.json': mock.MagicMock(),
    'stl.trex_stl_lib.utils.os': mock.MagicMock(),
    'stl.trex_stl_lib.utils.parsing_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.pwd': mock.MagicMock(),
    'stl.trex_stl_lib.utils.random': mock.MagicMock(),
    'stl.trex_stl_lib.utils.re': mock.MagicMock(),
    'stl.trex_stl_lib.utils.string': mock.MagicMock(),
    'stl.trex_stl_lib.utils.sys': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_tables': mock.MagicMock(),
    'stl.trex_stl_lib.utils.texttable': mock.MagicMock(),
    'stl.trex_stl_lib.warnings': mock.MagicMock(),
    'stl.trex_stl_lib.yaml': mock.MagicMock(),
    'stl.trex_stl_lib.zlib': mock.MagicMock(),
    'stl.trex_stl_lib.zmq': mock.MagicMock(),
}

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.vfw_vnf import FWApproxVnf
    from yardstick.network_services.nfvi.resource import ResourceProfile

TEST_FILE_YAML = 'nsb_test_case.yaml'


name = 'vnf__1'


@mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Process")
class TestFWApproxVnf(unittest.TestCase):
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
                    'host': '1.2.1.1',
                    'password': 'r00t',
                    'user': 'root',
                    'ip': '1.2.1.1'},
               'benchmark':
                   {'kpi': ['packets_in', 'packets_fwd', 'packets_dropped']},
               'connection-point': [{'type': 'VPORT', 'name': 'xe0'},
                                    {'type': 'VPORT', 'name': 'xe1'}],
               'id': 'FWApproxVnf', 'name': 'VPEVnfSsh'}]}}

    scenario_cfg = {'options': {'packetsize': 64, 'traffic_type': 4,
                                'rfc2544': {'allowed_drop_rate': '0.8 - 1'},
                                'vnf__1': {'rules': 'acl_1rule.yaml',
                                           'vnf_config': {'lb_config': 'SW',
                                                          'lb_count': 1,
                                                          'worker_config':
                                                              '1C/1T',
                                                          'worker_threads': 1}}
                                },
                    'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
                    'task_path': '/tmp',
                    'tc': 'tc_ipv4_1Mflow_64B_packetsize',
                    'runner': {'object': 'NetworkServiceTestCase',
                               'interval': 35,
                               'output_filename': '/tmp/yardstick.out',
                               'runner_id': 74476, 'duration': 400,
                               'type': 'Duration'},
                    'traffic_profile': 'ipv4_throughput_vfw.yaml',
                    'traffic_options': {'flow': 'ipv4_Packets_vfw.yaml',
                                        'imix': 'imix_voice.yaml'},
                    'type': 'ISB',
                    'nodes': {'tg__2': 'trafficgen_2.yardstick',
                              'tg__1': 'trafficgen_1.yardstick',
                              'vnf__1': 'vnf.yardstick'},
                    'topology': 'vpe-tg-topology-baremetal.yaml'}

    context_cfg = {'nodes': {'tg__2':
                             {'member-vnf-index': '3',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_2.yardstick',
                              'vnfd-id-ref': 'tg__2',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens513f0',
                                       'vld_id': 'public',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.20',
                                       'dst_mac': '00:00:00:00:00:01',
                                       'local_mac': '00:00:00:00:00:03',
                                       'dst_ip': '152.16.40.19',
                                       'driver': 'ixgbe',
                                       'vpci': '0000:02:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens513f1',
                                       'netmask': '255.255.255.0',
                                       'network': '202.16.100.0',
                                       'local_ip': '202.16.100.20',
                                       'local_mac': '00:1e:67:d0:60:5d',
                                       'driver': 'ixgbe',
                                       'vpci': '0000:02:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'l3fwd_vnf.yaml',
                              'user': 'root'},
                             'tg__1':
                             {'member-vnf-index': '1',
                              'role': 'TrafficGen',
                              'name': 'trafficgen_1.yardstick',
                              'vnfd-id-ref': 'tg__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens785f0',
                                       'vld_id': 'private',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.20',
                                       'dst_mac': '00:00:00:00:00:02',
                                       'local_mac': '00:00:00:00:00:04',
                                       'dst_ip': '152.16.100.19',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens785f1',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.21',
                                       'local_mac': '00:00:00:00:00:01',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'password': 'r00t',
                              'VNF model': 'tg_rfc2544_tpl.yaml',
                              'user': 'root'},
                             'vnf__1':
                             {'name': 'vnf.yardstick',
                              'vnfd-id-ref': 'vnf__1',
                              'ip': '1.2.1.1',
                              'interfaces':
                              {'xe0': {'local_iface_name': 'ens786f0',
                                       'vld_id': 'private',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.100.19',
                                       'dst_mac': '00:00:00:00:00:04',
                                       'local_mac': '00:00:00:00:00:02',
                                       'dst_ip': '152.16.100.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.0',
                                       'dpdk_port_num': 0},
                               'xe1': {'local_iface_name': 'ens786f1',
                                       'vld_id': 'public',
                                       'netmask': '255.255.255.0',
                                       'local_ip': '152.16.40.19',
                                       'dst_mac': '00:00:00:00:00:03',
                                       'local_mac': '00:00:00:00:00:01',
                                       'dst_ip': '152.16.40.20',
                                       'driver': 'i40e',
                                       'vpci': '0000:05:00.1',
                                       'dpdk_port_num': 1}},
                              'routing_table':
                              [{'netmask': '255.255.255.0',
                                'gateway': '152.16.100.20',
                                'network': '152.16.100.20',
                                'if': 'xe0'},
                               {'netmask': '255.255.255.0',
                                'gateway': '152.16.40.20',
                                'network': '152.16.40.20',
                                'if': 'xe1'}],
                              'member-vnf-index': '2',
                              'host': '1.2.1.1',
                              'role': 'vnf',
                              'user': 'root',
                              'nd_route_tbl':
                              [{'netmask': '112',
                                'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                                'network': '0064:ff9b:0:0:0:0:9810:6414',
                                'if': 'xe0'},
                               {'netmask': '112',
                                'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                                'network': '0064:ff9b:0:0:0:0:9810:2814',
                                'if': 'xe1'}],
                              'password': 'r00t',
                              'VNF model': 'vfw_vnf.yaml'}}}

    def test___init__(self, mock_process):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vfw_approx_vnf = FWApproxVnf(name, vnfd)
        self.assertIsNone(vfw_approx_vnf._vnf_process)

    STATS = """\
p vfw stats

VFW Stats
{"VFW_counters" : {"id" : "PIPELINE4", " pkts_received": 6007180, " pkts_fw_forwarded": 6007180, " pkts_drop_fw": 0, " pkts_acl_forwarded": 6007180, "pkts_drop_without_rule" : 0, "average_pkts_in_batch" : 31, "average_internal_time_in_clocks" : 17427, "average_external_time_in_clocks" : 261120, "total_time_measures" : 189829, "ct_packets_forwarded" : 6007148, "ct_packets_dropped" : 0, "bytes_processed ": 360430800, "ct_sessions" : {"active" : 130050, "open_attempt" : 130050, "re-open_attempt" : 0, "established" : 0, "closed" : 0, "timeout" : 0}, "ct_drops" : {"out_of_window" : 0, "invalid_conn" : 0, "invalid_state_transition" : 0 "RST" : 0}}
VFW TOTAL: pkts_received: 6007180, "pkts_fw_forwarded": 6007180, "pkts_drop_fw": 0, "fw_drops" : {"TTL_zero" : 0, "bad_size" : 0, "fragmented_packet" : 0, "unsupported_packet_types" : 0, "no_arp_entry" : 6007180}, "pkts_acl_forwarded": 6007180, "pkts_drop_without_rule": 0, "packets_last_sec" : 0, "average_packets_per_sec" : 0, "bytes_last_sec" : 0, "average_bytes_per_sec" : 0, "bytes_processed ": 360430800
"CT TOTAL: ct_packets_forwarded" : 6007180, " ct_packets_dropped" : 0, "ct_sessions" : {"active" : 130050, "open_attempt" : 130050, "re-open_attempt" : 0, "established" : 0, "closed" : 0, "timeout" : 0}, "ct_drops" : {"out_of_window" : 0, "invalid_conn" : 0, "invalid_state_transition" : 0 "RST" : 0}
Action ID: 00, packetCount: 2954633, byteCount: 177277980
Action ID: 01, packetCount: 3052547, byteCount: 183152820
pipeline> 

pipeline> 
"""  # noqa

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_collect_kpi(self, mock_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vfw_approx_vnf = FWApproxVnf(name, vnfd)
            vfw_approx_vnf.q_in = mock.MagicMock()
            vfw_approx_vnf.q_out = mock.MagicMock()
            vfw_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
            vfw_approx_vnf.resource = mock.Mock(autospec=ResourceProfile)
            vfw_approx_vnf.resource_helper = mock.MagicMock(
                **{'collect_kpi.return_value': {"core": {}}})
            vfw_approx_vnf.vnf_execute = mock.Mock(return_value=self.STATS)
            result = {
                'packets_dropped': 0,
                'packets_fwd': 6007180,
                'packets_in': 6007180,
                'collect_stats': {'core': {}},
            }
            self.assertEqual(result, vfw_approx_vnf.collect_kpi())

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_vnf_execute_command(self, mock_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vfw_approx_vnf = FWApproxVnf(name, vnfd)
            vfw_approx_vnf.q_in = mock.MagicMock()
            vfw_approx_vnf.q_out = mock.MagicMock()
            vfw_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
            cmd = "quit"
            self.assertEqual("", vfw_approx_vnf.vnf_execute(cmd))

    def test_get_stats(self, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vfw_approx_vnf = FWApproxVnf(name, vnfd)
            vfw_approx_vnf.q_in = mock.MagicMock()
            vfw_approx_vnf.q_out = mock.MagicMock()
            vfw_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
            vfw_approx_vnf.vnf_execute = mock.Mock(return_value=self.STATS)
            self.assertEqual(self.STATS, vfw_approx_vnf.get_stats())

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @mock.patch("yardstick.network_services.vnf_generic.vnf.vfw_vnf.hex")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.vfw_vnf.eval")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.vfw_vnf.open")
    def test_run_vfw(self, mock_open, eval, hex, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh_mock.run = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vfw_approx_vnf = FWApproxVnf(name, vnfd)
            vfw_approx_vnf._build_config = mock.MagicMock()
            vfw_approx_vnf.queue_wrapper = mock.MagicMock()
            vfw_approx_vnf.ssh_helper = mock.MagicMock()
            vfw_approx_vnf.ssh_helper.run = mock.MagicMock()
            vfw_approx_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
            vfw_approx_vnf.vnf_cfg = {'lb_config': 'SW',
                                      'lb_count': 1,
                                      'worker_config': '1C/1T',
                                      'worker_threads': 1}
            vfw_approx_vnf.all_options = {'traffic_type': '4',
                                          'topology': 'nsb_test_case.yaml'}
            vfw_approx_vnf._run()
            vfw_approx_vnf.ssh_helper.run.assert_called_once()

    @mock.patch("yardstick.network_services.vnf_generic.vnf.vfw_vnf.YangModel")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.vfw_vnf.find_relative_file")
    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    def test_instantiate(self, Context, mock_yang, mock_find, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vfw_approx_vnf = FWApproxVnf(name, vnfd)
            vfw_approx_vnf.ssh_helper = ssh
            vfw_approx_vnf.deploy_helper = mock.MagicMock()
            vfw_approx_vnf.resource_helper = mock.MagicMock()
            vfw_approx_vnf._build_config = mock.MagicMock()
            self.scenario_cfg['vnf_options'] = {'acl': {'cfg': "",
                                                        'rules': ""}}
            self.scenario_cfg.update({"nodes": {"vnf__1": ""}})
            self.assertIsNone(vfw_approx_vnf.instantiate(self.scenario_cfg,
                                                         self.context_cfg))

    def test_scale(self, mock_process):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vfw_approx_vnf = FWApproxVnf(name, vnfd)
        flavor = ""
        self.assertRaises(NotImplementedError, vfw_approx_vnf.scale, flavor)

    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    def test_terminate(self, mock_time, mock_process):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, "", ""))
            ssh.from_node.return_value = ssh_mock
            vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
            vfw_approx_vnf = FWApproxVnf(name, vnfd)
            vfw_approx_vnf._vnf_process = mock.MagicMock()
            vfw_approx_vnf._vnf_process.terminate = mock.Mock()
            vfw_approx_vnf.used_drivers = {"01:01.0": "i40e",
                                           "01:01.1": "i40e"}
            vfw_approx_vnf.vnf_execute = mock.Mock()
            vfw_approx_vnf.ssh_helper = ssh_mock
            vfw_approx_vnf.dpdk_nic_bind = "dpdk_nic_bind.py"
            vfw_approx_vnf._resource_collect_stop = mock.Mock()
            self.assertEqual(None, vfw_approx_vnf.terminate())

if __name__ == '__main__':
    unittest.main()
