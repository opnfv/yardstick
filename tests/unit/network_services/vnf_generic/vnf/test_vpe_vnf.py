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

import six.moves.configparser as configparser
import mock
from multiprocessing import Process, Queue

from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper

SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'

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
    from yardstick.network_services.vnf_generic.vnf.vpe_vnf import ConfigCreate
    from yardstick.network_services.nfvi.resource import ResourceProfile
    from yardstick.network_services.vnf_generic.vnf import vpe_vnf
    from yardstick.network_services.vnf_generic.vnf.vpe_vnf import VpeApproxVnf

from tests.unit.network_services.vnf_generic.vnf.test_base import FileAbsPath
from tests.unit.network_services.vnf_generic.vnf.test_base import mock_ssh


TEST_FILE_YAML = 'nsb_test_case.yaml'

NAME = 'vnf_1'

PING_OUTPUT_1 = "Pkts in: 101\r\n\tPkts dropped by AH: 100\r\n\tPkts dropped by other: 100"

MODULE_PATH = FileAbsPath(__file__)
get_file_abspath = MODULE_PATH.get_path


class TestConfigCreate(unittest.TestCase):

    def test___init__(self):
        config_create = ConfigCreate([0], [1], 2)
        self.assertEqual(config_create.priv_ports, [0])
        self.assertEqual(config_create.pub_ports, [1])
        self.assertEqual(config_create.socket, 2)

    def test_vpe_initialize(self):
        config_create = ConfigCreate([0], [1], 2)
        config = configparser.ConfigParser()
        config_create.vpe_initialize(config)
        self.assertEqual(config.get('EAL', 'log_level'), '0')
        self.assertEqual(config.get('PIPELINE0', 'type'), 'MASTER')
        self.assertEqual(config.get('PIPELINE0', 'core'), 's2C0')
        self.assertEqual(config.get('MEMPOOL0', 'pool_size'), '256K')
        self.assertEqual(config.get('MEMPOOL1', 'pool_size'), '2M')

    def test_vpe_rxq(self):
        config_create = ConfigCreate([0], [1, 2], 3)
        config = configparser.ConfigParser()
        config_create.vpe_rxq(config)
        self.assertEqual(config.get('RXQ1.0', 'mempool'), 'MEMPOOL1')
        self.assertEqual(config.get('RXQ2.0', 'mempool'), 'MEMPOOL1')

    def test_get_sink_swq(self):
        config_create = ConfigCreate([0], [1], 2)
        config = configparser.ConfigParser()
        config.add_section('PIPELINE0')
        config.set('PIPELINE0', 'key1', 'value1')
        config.set('PIPELINE0', 'key2', 'value2 SINK')
        config.set('PIPELINE0', 'key3', 'TM value3')
        config.set('PIPELINE0', 'key4', 'value4')
        config.set('PIPELINE0', 'key5', 'the SINK value5')

        self.assertEqual(config_create.get_sink_swq(config, 'PIPELINE0', 'key1', 5), 'SWQ-1')
        self.assertEqual(config_create.get_sink_swq(config, 'PIPELINE0', 'key2', 5), 'SWQ-1 SINK0')
        self.assertEqual(config_create.get_sink_swq(config, 'PIPELINE0', 'key3', 5), 'SWQ-1 TM5')
        config_create.sw_q += 1
        self.assertEqual(config_create.get_sink_swq(config, 'PIPELINE0', 'key4', 5), 'SWQ0')
        self.assertEqual(config_create.get_sink_swq(config, 'PIPELINE0', 'key5', 5), 'SWQ0 SINK1')

    def test_generate_vpe_script(self):
        vpe_config_vnf = ConfigCreate([0], [0], 0)
        intf = [
            {
                "virtual-interface": {
                    "dst_ip": "1.1.1.1",
                    "dst_mac": "00:00:00:00:00:00:02",
                },
            },
        ]
        result = vpe_config_vnf.generate_vpe_script(intf)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '')

    def test_create_vpe_config(self):
        priv_ports = [
            {
                'index': 0,
                'dpdk_port_num': 1,
                'peer_intf': {
                    'dpdk_port_num': 2,
                    'index': 3,
                },
            },
        ]

        pub_ports = [
            {
                'index': 2,
                'dpdk_port_num': 3,
                'peer_intf': {
                    'dpdk_port_num': 0,
                    'index': 1,
                },
            },
        ]

        config_create = ConfigCreate(priv_ports, pub_ports, 23)
        curr_path = os.path.dirname(os.path.abspath(__file__))
        vpe_cfg = "samples/vnf_samples/nsut/vpe/vpe_config"
        vnf_cfg = os.path.join(curr_path, "../../../../..", vpe_cfg)
        config_create.create_vpe_config(vnf_cfg)
        os.system("git checkout -- %s" % vnf_cfg)


@mock.patch('yardstick.network_services.vnf_generic.vnf.sample_vnf.time')
class TestVpeApproxVnf(unittest.TestCase):

    VNFD_0 = {
        'short-name': 'VpeVnf',
        'vdu': [
            {
                'routing_table': [
                    {
                        'network': '152.16.100.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'if': 'xe0',
                    },
                    {
                        'network': '152.16.40.20',
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'if': 'xe1',
                    },
                ],
                'description': 'VPE approximation using DPDK',
                'name': 'vpevnf-baremetal',
                'nd_route_tbl': [
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0',
                    },
                    {
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1',
                    },
                ],
                'id': 'vpevnf-baremetal',
                'external-interface': [
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:04',
                            'vpci': '0000:05:00.0',
                            'local_ip': '152.16.100.19',
                            'type': 'PCI-PASSTHROUGH',
                            'vld_id': '',
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': '0',
                            'bandwidth': '10 Gbps',
                            'driver': "i40e",
                            'dst_ip': '152.16.100.20',
                            'local_iface_name': 'xe0',
                            'local_mac': '00:00:00:00:00:02',
                        },
                        'vnfd-connection-point-ref': 'xe0',
                        'name': 'xe0',
                    },
                    {
                        'virtual-interface': {
                            'dst_mac': '00:00:00:00:00:03',
                            'vpci': '0000:05:00.1',
                            'local_ip': '152.16.40.19',
                            'type': 'PCI-PASSTHROUGH',
                            'vld_id': '',
                            'driver': "i40e",
                            'netmask': '255.255.255.0',
                            'dpdk_port_num': '1',
                            'bandwidth': '10 Gbps',
                            'dst_ip': '152.16.40.20',
                            'local_iface_name': 'xe1',
                            'local_mac': '00:00:00:00:00:01',
                        },
                        'vnfd-connection-point-ref': 'xe1',
                        'name': 'xe1',
                    },
                ],
            },
        ],
        'description': 'Vpe approximation using DPDK',
        'mgmt-interface': {
            'vdu-id': 'vpevnf-baremetal',
            'host': '1.2.1.1',
            'password': 'r00t',
            'user': 'root',
            'ip': '1.2.1.1',
        },
        'benchmark': {
            'kpi': [
                'packets_in',
                'packets_fwd',
                'packets_dropped',
            ],
        },
        'connection-point': [
            {
                'type': 'VPORT',
                'name': 'xe0',
            },
            {
                'type': 'VPORT',
                'name': 'xe1',
            },
        ],
        'id': 'VpeApproxVnf',
        'name': 'VPEVnfSsh',
    }

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ],
        },
    }

    SCENARIO_CFG = {
        'options': {
            'packetsize': 64,
            'traffic_type': 4 ,
            'rfc2544': {
                'allowed_drop_rate': '0.8 - 1',
            },
            'vnf__1': {
                'cfg': 'acl_1rule.yaml',
                'vnf_config': {
                    'lb_config': 'SW',
                    'lb_count': 1,
                    'worker_config':
                    '1C/1T',
                    'worker_threads': 1,
                },
            }
        },
        'task_id': 'a70bdf4a-8e67-47a3-9dc1-273c14506eb7',
        'tc': 'tc_ipv4_1Mflow_64B_packetsize',
        'runner': {
            'object': 'NetworkServiceTestCase',
            'interval': 35,
            'output_filename': '/tmp/yardstick.out',
            'runner_id': 74476,
            'duration': 400,
            'type': 'Duration',
        },
        'traffic_profile': 'ipv4_throughput_vpe.yaml',
        'traffic_options': {
            'flow': 'ipv4_Packets_vpe.yaml',
            'imix': 'imix_voice.yaml',
        },
        'type': 'ISB',
        'nodes': {
            'tg__2': 'trafficgen_2.yardstick',
            'tg__1': 'trafficgen_1.yardstick',
            'vnf__1': 'vnf.yardstick',
        },
        'topology': 'vpe-tg-topology-baremetal.yaml',
    }

    CONTEXT_CFG = {
        'nodes': {
            'tg__2': {
                'member-vnf-index': '3',
                'role': 'TrafficGen',
                'name': 'trafficgen_2.yardstick',
                'vnfd-id-ref': 'tg__2',
                'ip': '1.2.1.1',
                'interfaces': {
                    'xe0': {
                        'local_iface_name': 'ens513f0',
                        'vld_id': 'public',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.40.20',
                        'dst_mac': '00:00:00:00:00:01',
                        'local_mac': '00:00:00:00:00:03',
                        'dst_ip': '152.16.40.19',
                        'driver': 'ixgbe',
                        'vpci': '0000:02:00.0',
                        'dpdk_port_num': 0,
                    },
                    'xe1': {
                        'local_iface_name': 'ens513f1',
                        'netmask': '255.255.255.0',
                        'network': '202.16.100.0',
                        'local_ip': '202.16.100.20',
                        'local_mac': '00:1e:67:d0:60:5d',
                        'driver': 'ixgbe',
                        'vpci': '0000:02:00.1',
                        'dpdk_port_num': 1,
                    },
                },
                'password': 'r00t',
                'VNF model': 'l3fwd_vnf.yaml',
                'user': 'root',
            },
            'tg__1': {
                'member-vnf-index': '1',
                'role': 'TrafficGen',
                'name': 'trafficgen_1.yardstick',
                'vnfd-id-ref': 'tg__1',
                'ip': '1.2.1.1',
                'interfaces': {
                    'xe0': {
                        'local_iface_name': 'ens785f0',
                        'vld_id': 'private',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.100.20',
                        'dst_mac': '00:00:00:00:00:02',
                        'local_mac': '00:00:00:00:00:04',
                        'dst_ip': '152.16.100.19',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.0',
                        'dpdk_port_num': 0,
                    },
                    'xe1': {
                        'local_iface_name': 'ens785f1',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.100.21',
                        'local_mac': '00:00:00:00:00:01',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.1',
                        'dpdk_port_num': 1,
                    },
                },
                'password': 'r00t',
                'VNF model': 'tg_rfc2544_tpl.yaml',
                'user': 'root',
            },
            'vnf__1': {
                'name': 'vnf.yardstick',
                'vnfd-id-ref': 'vnf__1',
                'ip': '1.2.1.1',
                'interfaces': {
                    'xe0': {
                        'local_iface_name': 'ens786f0',
                        'vld_id': 'private',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.100.19',
                        'dst_mac': '00:00:00:00:00:04',
                        'local_mac': '00:00:00:00:00:02',
                        'dst_ip': '152.16.100.20',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.0',
                        'dpdk_port_num': 0,
                    },
                    'xe1': {
                        'local_iface_name': 'ens786f1',
                        'vld_id': 'public',
                        'netmask': '255.255.255.0',
                        'local_ip': '152.16.40.19',
                        'dst_mac': '00:00:00:00:00:03',
                        'local_mac': '00:00:00:00:00:01',
                        'dst_ip': '152.16.40.20',
                        'driver': 'i40e',
                        'vpci': '0000:05:00.1',
                        'dpdk_port_num': 1,
                    },
                },
                'routing_table': [
                    {
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.100.20',
                        'network': '152.16.100.20',
                        'if': 'xe0',
                    },
                    {
                        'netmask': '255.255.255.0',
                        'gateway': '152.16.40.20',
                        'network': '152.16.40.20',
                        'if': 'xe1',
                    },
                ],
                'member-vnf-index': '2',
                'host': '1.2.1.1',
                'role': 'vnf',
                'user': 'root',
                'nd_route_tbl': [
                    {
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:6414',
                        'network': '0064:ff9b:0:0:0:0:9810:6414',
                        'if': 'xe0',
                    },
                    {
                        'netmask': '112',
                        'gateway': '0064:ff9b:0:0:0:0:9810:2814',
                        'network': '0064:ff9b:0:0:0:0:9810:2814',
                        'if': 'xe1',
                    },
                ],
                'password': 'r00t',
                'VNF model': 'vpe_vnf.yaml',
            },
        },
    }

    def test___init__(self, _):
        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.assertIsNone(vpe_approx_vnf._vnf_process)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi_sa_not_running(self, ssh, _):
        mock_ssh(ssh)

        resource = mock.Mock(autospec=ResourceProfile)
        resource.check_if_sa_running.return_value = False, 'error'
        resource.amqp_collect_nfvi_kpi.return_value = {'foo': 234}

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf.q_in = mock.MagicMock()
        vpe_approx_vnf.q_out = mock.MagicMock()
        vpe_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        vpe_approx_vnf.resource_helper.resource = resource

        expected = {
            'pkt_in_down_stream': 0,
            'pkt_in_up_stream': 0,
            'pkt_drop_down_stream': 0,
            'pkt_drop_up_stream': 0,
            'collect_stats': {'core': {}},
        }
        self.assertEqual(vpe_approx_vnf.collect_kpi(), expected)

    @mock.patch(SSH_HELPER)
    def test_collect_kpi_sa_running(self, ssh, _):
        mock_ssh(ssh)

        resource = mock.Mock(autospec=ResourceProfile)
        resource.check_if_sa_running.return_value = True, 'good'
        resource.amqp_collect_nfvi_kpi.return_value = {'foo': 234}

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf.q_in = mock.MagicMock()
        vpe_approx_vnf.q_out = mock.MagicMock()
        vpe_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        vpe_approx_vnf.resource_helper.resource = resource

        expected = {
            'pkt_in_down_stream': 0,
            'pkt_in_up_stream': 0,
            'pkt_drop_down_stream': 0,
            'pkt_drop_up_stream': 0,
            'collect_stats': {'core': {'foo': 234}},
        }
        self.assertEqual(vpe_approx_vnf.collect_kpi(), expected)

    @mock.patch(SSH_HELPER)
    def test_vnf_execute(self, ssh, _):
        mock_ssh(ssh)
        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf.q_in = mock.MagicMock()
        vpe_approx_vnf.q_out = mock.MagicMock()
        vpe_approx_vnf.q_out.qsize = mock.Mock(return_value=0)
        self.assertEqual(vpe_approx_vnf.vnf_execute("quit", 0), '')

    @mock.patch(SSH_HELPER)
    def test_run_vpe(self, ssh, _):
        mock_ssh(ssh)

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf.tc_file_name = get_file_abspath(TEST_FILE_YAML)
        vpe_approx_vnf.generate_port_pairs = mock.Mock()
        vpe_approx_vnf.tg_port_pairs = [[[0], [1]]]
        vpe_approx_vnf.vnf_port_pairs = [[[0], [1]]]
        vpe_approx_vnf.vnf_cfg = {
            'lb_config': 'SW',
            'lb_count': 1,
            'worker_config': '1C/1T',
            'worker_threads': 1,
        }
        vpe_approx_vnf.scenario_helper.scenario_cfg = {
            'options': {
                NAME: {
                    'traffic_type': '4',
                    'topology': 'nsb_test_case.yaml',
                }
            }
        }
        vpe_approx_vnf.topology = "nsb_test_case.yaml"
        vpe_approx_vnf.nfvi_type = "baremetal"
        vpe_approx_vnf._provide_config_file = mock.Mock()

        self.assertIsInstance(vpe_approx_vnf.ssh_helper, mock.Mock)
        self.assertIsNone(vpe_approx_vnf._run())

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate(self, ssh, _):
        mock_ssh(ssh)

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = True
        mock_process.exitcode = 432

        mock_q_out = mock.Mock(autospec=Queue)
        mock_q_out.get.side_effect = iter(["pipeline>"])
        mock_q_out.qsize.side_effect = range(1, -1, -1)

        mock_resource = mock.MagicMock()

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf._vnf_process = mock_process
        vpe_approx_vnf.q_out = mock_q_out
        vpe_approx_vnf.queue_wrapper = mock.Mock(autospec=QueueFileWrapper)
        vpe_approx_vnf.resource_helper.resource = mock_resource

        vpe_approx_vnf.q_out.put("pipeline>")
        self.assertEqual(vpe_approx_vnf.wait_for_instantiate(), 432)

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_fragmented(self, ssh, _):
        mock_ssh(ssh)

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = True
        mock_process.exitcode = 432

        # test that fragmented pipeline prompt is recognized
        mock_q_out = mock.Mock(autospec=Queue)
        mock_q_out.get.side_effect = iter(["wow pipel", "ine>"])
        mock_q_out.qsize.side_effect = range(2, -1, -1)

        mock_resource = mock.MagicMock()

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf._vnf_process = mock_process
        vpe_approx_vnf.q_out = mock_q_out
        vpe_approx_vnf.queue_wrapper = mock.Mock(autospec=QueueFileWrapper)
        vpe_approx_vnf.resource_helper.resource = mock_resource

        self.assertEqual(vpe_approx_vnf.wait_for_instantiate(), 432)

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_crash(self, ssh, _):
        mock_ssh(ssh, exec_result=(1, "", ""))

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = False
        mock_process.exitcode = 432

        mock_resource = mock.MagicMock()

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf._vnf_process = mock_process
        vpe_approx_vnf.resource_helper.resource = mock_resource

        with self.assertRaises(RuntimeError) as raised:
            vpe_approx_vnf.wait_for_instantiate()

        self.assertIn('VNF process died', str(raised.exception))

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_panic(self, ssh, _):
        mock_ssh(ssh, exec_result=(1, "", ""))

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = True
        mock_process.exitcode = 432

        mock_resource = mock.MagicMock()

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf._vnf_process = mock_process
        vpe_approx_vnf.resource_helper.resource = mock_resource

        vpe_approx_vnf.q_out.put("PANIC")
        with self.assertRaises(RuntimeError) as raised:
            vpe_approx_vnf.wait_for_instantiate()

        self.assertIn('Error starting', str(raised.exception))

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_panic_fragmented(self, ssh, _):
        mock_ssh(ssh, exec_result=(1, "", ""))

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = True
        mock_process.exitcode = 432

        # test that fragmented PANIC is recognized
        mock_q_out = mock.Mock(autospec=Queue)
        mock_q_out.get.side_effect = iter(["omg PA", "NIC this is bad"])
        mock_q_out.qsize.side_effect = range(2, -1, -1)

        mock_resource = mock.MagicMock()

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf._vnf_process = mock_process
        vpe_approx_vnf.q_out = mock_q_out
        vpe_approx_vnf.resource_helper.resource = mock_resource

        with self.assertRaises(RuntimeError) as raised:
            vpe_approx_vnf.wait_for_instantiate()

        self.assertIn('Error starting', str(raised.exception))

    @mock.patch(SSH_HELPER)
    def old_test__get_ports_gateway(self, ssh, _):
        mock_ssh(ssh)

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'acl': {'cfg': "", 'rules': ""}}
        vpe_approx_vnf._run_vpe = mock.Mock(return_value=0)
        vpe_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
        vpe_approx_vnf.deploy_acl_vnf = mock.Mock(return_value=0)
        vpe_approx_vnf.q_out.put("pipeline>")
        vpe_vnf.WAIT_TIME = 0
        vpe_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2, 3])
        vpe_approx_vnf.resource = mock.MagicMock()
        vpe_approx_vnf.resource.initiate_systemagent = mock.Mock()
        vpe_approx_vnf.resource.stop = mock.Mock()
        vpe_approx_vnf.resource.amqp_process_for_nfvi_kpi = mock.Mock()
        vpe_approx_vnf.resource.check_if_sa_running(return_value=[1])
        vpe_approx_vnf.resource.amqp_collect_nfvi_kpi(return_value={})
        self.assertEqual('152.16.100.20', vpe_approx_vnf._get_ports_gateway('xe0'))

    @mock.patch(SSH_HELPER)
    def old_test__resource_collect_start(self, ssh, _):
        mock_ssh(ssh)

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'acl': {'cfg': "", 'rules': ""}}
        vpe_approx_vnf._run_acl = mock.Mock(return_value=0)
        vpe_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
        vpe_approx_vnf.deploy_vpe_vnf = mock.Mock(return_value=0)
        vpe_approx_vnf.q_out.put("pipeline>")
        vpe_vnf.WAIT_TIME = 0
        vpe_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2, 3])
        vpe_approx_vnf.resource = mock.MagicMock()
        vpe_approx_vnf.resource.initiate_systemagent = mock.Mock()
        vpe_approx_vnf.resource.start = mock.Mock()
        vpe_approx_vnf.resource.amqp_process_for_nfvi_kpi = mock.Mock()
        self.assertIsNone(vpe_approx_vnf._resource_collect_start())

    @mock.patch("yardstick.ssh.SSH")
    def old_test__resource_collect_stop(self, ssh, _):
        mock_ssh(ssh)

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'acl': {'cfg': "", 'rules': ""}}
        vpe_approx_vnf._run_acl = mock.Mock(return_value=0)
        vpe_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
        vpe_approx_vnf.deploy_vpe_vnf = mock.Mock(return_value=0)
        vpe_approx_vnf.q_out.put("pipeline>")
        vpe_vnf.WAIT_TIME = 0
        vpe_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2, 3])
        vpe_approx_vnf.resource = mock.MagicMock()
        vpe_approx_vnf.resource.initiate_systemagent = mock.Mock()
        vpe_approx_vnf.resource.stop = mock.Mock()
        vpe_approx_vnf.resource.amqp_process_for_nfvi_kpi = mock.Mock()
        self.assertIsNone(vpe_approx_vnf._resource_collect_stop())

    @mock.patch("yardstick.ssh.SSH")
    def old_test__collect_resource_kpi(self, ssh, _):
        mock_ssh(ssh)

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'acl': {'cfg': "", 'rules': ""}}
        vpe_approx_vnf._run_acl = mock.Mock(return_value=0)
        vpe_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
        vpe_approx_vnf.deploy_vpe_vnf = mock.Mock(return_value=0)
        vpe_approx_vnf.q_out.put("pipeline>")
        vpe_vnf.WAIT_TIME = 0
        vpe_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2, 3])
        vpe_approx_vnf.resource = mock.MagicMock()
        vpe_approx_vnf.resource.initiate_systemagent = mock.Mock()
        vpe_approx_vnf.resource.stop = mock.Mock()
        vpe_approx_vnf.resource.amqp_process_for_nfvi_kpi = mock.Mock()
        vpe_approx_vnf.resource.check_if_sa_running(return_value=[1])
        vpe_approx_vnf.resource.amqp_collect_nfvi_kpi(return_value={})
        self.assertIsNotNone(vpe_approx_vnf._collect_resource_kpi())

    @mock.patch("yardstick.ssh.SSH")
    def old_test__get_cpu_sibling_list(self, ssh, _):
        mock_ssh(ssh, exec_result=(0, "1,2", ""))

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['vnf_options'] = {'acl': {'cfg': "", 'rules': ""}}
        vpe_approx_vnf._run_acl = mock.Mock(return_value=0)
        vpe_approx_vnf._parse_rule_file = mock.Mock(return_value={})
        vpe_approx_vnf.get_nfvi_type = mock.Mock(return_value="baremetal")
        vpe_approx_vnf.deploy_vpe_vnf = mock.Mock(return_value=0)
        vpe_approx_vnf.q_out.put("pipeline>")
        vpe_vnf.WAIT_TIME = 0
        vpe_approx_vnf._validate_cpu_cfg = mock.Mock(return_value=[1, 2, 3])
        vpe_approx_vnf.resource = mock.MagicMock()
        vpe_approx_vnf.resource.initiate_systemagent = mock.Mock()
        vpe_approx_vnf.resource.stop = mock.Mock()
        vpe_approx_vnf.resource.amqp_process_for_nfvi_kpi = mock.Mock()
        vpe_approx_vnf.resource.check_if_sa_running(return_value=[1])
        vpe_approx_vnf.resource.amqp_collect_nfvi_kpi(return_value={})
        vpe_approx_vnf.generate_port_pairs = mock.Mock()
        vpe_approx_vnf.tg_port_pairs = [[[0], [1]]]
        vpe_approx_vnf.topology = ""

        self.assertIsNotNone(vpe_approx_vnf._get_cpu_sibling_list())

    def old_test_get_nfvi_type(self, _):
        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.SCENARIO_CFG['tc'] = self._get_file_abspath("nsb_test_case")
        vpe_approx_vnf.nfvi_context = {}
        self.assertEqual("baremetal", vpe_approx_vnf.get_nfvi_type(self.SCENARIO_CFG))

    def test_scale(self, _):
        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        with self.assertRaises(NotImplementedError):
            vpe_approx_vnf.scale('')

    @mock.patch("yardstick.ssh.SSH")
    def old_test_setup_vnf_environment(self, ssh, _):
        mock_ssh(ssh)

        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        self.assertIsNone(vpe_approx_vnf._setup_vnf_environment())

    def test_terminate(self, _):
        vpe_approx_vnf = VpeApproxVnf(NAME, self.VNFD_0)
        vpe_approx_vnf.vnf_execute = mock.Mock()
        vpe_approx_vnf._vnf_process = mock.MagicMock()
        vpe_approx_vnf._vnf_process.terminate = mock.Mock()
        vpe_approx_vnf._resource_collect_stop = mock.Mock()
        vpe_approx_vnf.resource_helper = mock.MagicMock()
        vpe_approx_vnf.ssh_helper = mock.MagicMock()

        self.assertIsNone(vpe_approx_vnf.terminate())

    @mock.patch('yardstick.network_services.vnf_generic.vnf.vpe_vnf.os')
    @mock.patch("yardstick.ssh.SSH")
    def old_test__provide_config_file(self, ssh, *_):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vpe_approx_vnf = VpeApproxVnf(NAME, vnfd)
        vpe_approx_vnf._read_yang_model_config = mock.Mock(return_value=1)
        vpe_approx_vnf._get_converted_yang_entries = mock.Mock(return_value=1)
        prefix = 'acl_config'
        template = mock.MagicMock()
        self.assertIsNotNone(vpe_approx_vnf._provide_config_file(prefix, template))

if __name__ == '__main__':
    unittest.main()
