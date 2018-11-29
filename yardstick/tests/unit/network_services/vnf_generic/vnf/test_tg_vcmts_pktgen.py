# Copyright (c) 2019 Viosoft Corporation
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

import unittest
import mock
import socket
import threading
import time
import os
import copy

from yardstick.benchmark.contexts import base as ctx_base
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services.vnf_generic.vnf import tg_vcmts_pktgen


NAME = "tg__0"


class TestPktgenHelper(unittest.TestCase):

    def test___init__(self):
        pktgen_helper = tg_vcmts_pktgen.PktgenHelper("localhost", 23000)
        self.assertEqual(pktgen_helper.host, "localhost")
        self.assertEqual(pktgen_helper.port, 23000)
        self.assertFalse(pktgen_helper.connected)

    def _run_fake_server(self):
        server_sock = socket.socket()
        server_sock.bind(('localhost', 23000))
        server_sock.listen(0)
        client_socket, _ = server_sock.accept()
        client_socket.close()
        server_sock.close()

    def test__connect(self):
        pktgen_helper = tg_vcmts_pktgen.PktgenHelper("localhost", 23000)
        self.assertFalse(pktgen_helper._connect())
        server_thread = threading.Thread(target=self._run_fake_server)
        server_thread.start()
        time.sleep(0.5)
        self.assertTrue(pktgen_helper._connect())
        pktgen_helper._sock.close()
        server_thread.join()

    @mock.patch('yardstick.network_services.vnf_generic.vnf.tg_vcmts_pktgen.time')
    def test_connect(self, *args):
        pktgen_helper = tg_vcmts_pktgen.PktgenHelper("localhost", 23000)
        pktgen_helper.connected = True
        self.assertTrue(pktgen_helper.connect())
        pktgen_helper.connected = False

        pktgen_helper._connect = mock.MagicMock(return_value=True)
        self.assertTrue(pktgen_helper.connect())
        self.assertTrue(pktgen_helper.connected)

        pktgen_helper = tg_vcmts_pktgen.PktgenHelper("localhost", 23000)
        pktgen_helper._connect = mock.MagicMock(return_value=False)
        self.assertFalse(pktgen_helper.connect())
        self.assertFalse(pktgen_helper.connected)

    def test_send_command(self):
        pktgen_helper = tg_vcmts_pktgen.PktgenHelper("localhost", 23000)
        with self.assertRaises(IOError):
            pktgen_helper.send_command("")

        pktgen_helper.connected = True
        self.assertFalse(pktgen_helper.send_command(""))

        pktgen_helper._sock = mock.MagicMock()
        self.assertTrue(pktgen_helper.send_command(""))


class TestVcmtsPktgenSetupEnvHelper(unittest.TestCase):

    PKTGEN_PARAMETERS = "export LUA_PATH=/vcmts/Pktgen.lua;"\
                        "export CMK_PROC_FS=/host/proc;"\
                        "  /pktgen-config/setup.sh 0 4 18:02.0 "\
                        "18:02.1 18:02.2 18:02.3 00:00.0 00:00.0 "\
                        "00:00.0 00:00.0 imix1_100cms_1ofdm.pcap "\
                        "imix1_100cms_1ofdm.pcap imix1_100cms_1ofdm.pcap "\
                        "imix1_100cms_1ofdm.pcap imix1_100cms_1ofdm.pcap "\
                        "imix1_100cms_1ofdm.pcap imix1_100cms_1ofdm.pcap "\
                        "imix1_100cms_1ofdm.pcap"

    OPTIONS = {
        "pktgen_values": "/tmp/pktgen_values.yaml",
        "tg__0": {
            "pktgen_id": 0
        },
        "vcmts_influxdb_ip": "10.80.5.150",
        "vcmts_influxdb_port": 8086,
        "vcmtsd_values": "/tmp/vcmtsd_values.yaml",
        "vnf__0": {
            "sg_id": 0,
            "stream_dir": "us"
        },
        "vnf__1": {
            "sg_id": 0,
            "stream_dir": "ds"
        }
    }

    def setUp(self):
        vnfd_helper = VnfdHelper(
            TestVcmtsPktgen.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS

        self.setup_helper = tg_vcmts_pktgen.VcmtsPktgenSetupEnvHelper(
            vnfd_helper, ssh_helper, scenario_helper)

    def test_generate_pcap_filename(self):
        pcap_file_name = self.setup_helper.generate_pcap_filename(\
                            TestVcmtsPktgen.PKTGEN_POD_VALUES[0]['ports'][0])
        self.assertEquals(pcap_file_name, "imix1_100cms_1ofdm.pcap")

    def test_find_port_cfg(self):
        port_cfg = self.setup_helper.find_port_cfg(\
                TestVcmtsPktgen.PKTGEN_POD_VALUES[0]['ports'], "port_0")
        self.assertIsNotNone(port_cfg)

        port_cfg = self.setup_helper.find_port_cfg(\
                TestVcmtsPktgen.PKTGEN_POD_VALUES[0]['ports'], "port_8")
        self.assertIsNone(port_cfg)

    def test_build_pktgen_parameters(self):
        parameters = self.setup_helper.build_pktgen_parameters(
            TestVcmtsPktgen.PKTGEN_POD_VALUES[0])
        self.assertEquals(parameters, self.PKTGEN_PARAMETERS)

    def test_start_pktgen(self):
        self.setup_helper.ssh_helper = mock.MagicMock()
        self.setup_helper.start_pktgen(TestVcmtsPktgen.PKTGEN_POD_VALUES[0])
        self.setup_helper.ssh_helper.send_command.assert_called_with(
            self.PKTGEN_PARAMETERS)

    def test_setup_vnf_environment(self):
        self.assertIsNone(self.setup_helper.setup_vnf_environment())

class TestVcmtsPktgen(unittest.TestCase):

    VNFD = {'vnfd:vnfd-catalog':
            {'vnfd':
            [{
            "benchmark": {
                "kpi": [
                    "upstream/bits_per_second"
                ]
            },
            "connection-point": [
                {
                    "name": "xe0",
                    "type": "VPORT"
                },
                {
                    "name": "xe1",
                    "type": "VPORT"
                }
            ],
            "description": "vCMTS Pktgen Kubernetes",
            "id": "VcmtsPktgen",
            "mgmt-interface": {
                "ip": "192.168.24.150",
                "key_filename": "/tmp/yardstick_key-a3b663c2",
                "user": "root",
                "vdu-id": "vcmtspktgen-kubernetes"
            },
            "name": "vcmtspktgen",
            "short-name": "vcmtspktgen",
            "vdu": [
                {
                    "description": "vCMTS Pktgen Kubernetes",
                    "external-interface": [],
                    "id": "vcmtspktgen-kubernetes",
                    "name": "vcmtspktgen-kubernetes"
                }
            ],
            "vm-flavor": {
                "memory-mb": "4096",
                "vcpu-count": "4"
            }
        }]
    }}

    PKTGEN_POD_VALUES = [
        {
            "num_ports": "4",
            "pktgen_id": "0",
            "ports": [
                {
                    "net_pktgen": "18:02.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_0": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "18:02.1",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_1": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "18:02.2",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_2": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "18:02.3",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_3": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_4": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_5": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_6": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_7": "",
                    "traffic_type": "imix1"
                }
            ]
        },
        {
            "num_ports": 4,
            "pktgen_id": 1,
            "ports": [
                {
                    "net_pktgen": "18:0a.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_0": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "18:0a.1",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_1": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "18:0a.2",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_2": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "18:0a.3",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_3": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_4": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_5": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_6": "",
                    "traffic_type": "imix1"
                },
                {
                    "net_pktgen": "00:00.0",
                    "num_ofdm": "1",
                    "num_subs": "100",
                    "port_7": "",
                    "traffic_type": "imix1"
                }
            ]
        }
    ]

    SCENARIO_CFG = {
        "nodes": {
            "tg__0": "pktgen0-k8syardstick-a3b663c2",
            "vnf__0": "vnf0us-k8syardstick-a3b663c2",
            "vnf__1": "vnf0ds-k8syardstick-a3b663c2"
        },
        "options": {
            "pktgen_values": "/tmp/pktgen_values.yaml",
            "tg__0": {
                "pktgen_id": 0
            },
            "vcmts_influxdb_ip": "10.80.5.150",
            "vcmts_influxdb_port": 8086,
            "vcmtsd_values": "/tmp/vcmtsd_values.yaml",
            "vnf__0": {
                "sg_id": 0,
                "stream_dir": "us"
            },
            "vnf__1": {
                "sg_id": 0,
                "stream_dir": "ds"
            }
        },
        "task_id": "a3b663c2-e616-4777-b6d0-ec2ea7a06f42",
        "task_path": "samples/vnf_samples/nsut/cmts",
        "tc": "tc_vcmts_k8s_pktgen",
        "topology": "k8s_vcmts_topology.yaml",
        "traffic_profile": "../../traffic_profiles/fixed.yaml",
        "type": "NSPerf"
    }

    CONTEXT_CFG = {
        "networks": {
            "flannel": {
                "name": "flannel"
            },
            "xe0": {
                "name": "xe0"
            },
            "xe1": {
                "name": "xe1"
            }
        },
        "nodes": {
            "tg__0": {
                "VNF model": "../../vnf_descriptors/tg_vcmts_tpl.yaml",
                "interfaces": {
                    "flannel": {
                        "local_ip": "192.168.24.150",
                        "local_mac": None,
                        "network_name": "flannel"
                    },
                    "xe0": {
                        "local_ip": "192.168.24.150",
                        "local_mac": None,
                        "network_name": "xe0"
                    },
                    "xe1": {
                        "local_ip": "192.168.24.150",
                        "local_mac": None,
                        "network_name": "xe1"
                    }
                },
                "ip": "192.168.24.150",
                "key_filename": "/tmp/yardstick_key-a3b663c2",
                "member-vnf-index": "1",
                "name": "pktgen0-k8syardstick-a3b663c2",
                "private_ip": "192.168.24.150",
                "service_ports": [
                    {
                        "name": "ssh",
                        "node_port": 60270,
                        "port": 22,
                        "protocol": "TCP",
                        "target_port": 22
                    },
                    {
                        "name": "lua",
                        "node_port": 43619,
                        "port": 22022,
                        "protocol": "TCP",
                        "target_port": 22022
                    }
                ],
                "ssh_port": 60270,
                "user": "root",
                "vnfd-id-ref": "tg__0"
            },
            "vnf__0": {
                "VNF model": "../../vnf_descriptors/vnf_vcmts_tpl.yaml",
                "interfaces": {
                    "flannel": {
                        "local_ip": "192.168.100.132",
                        "local_mac": None,
                        "network_name": "flannel"
                    },
                    "xe0": {
                        "local_ip": "192.168.100.132",
                        "local_mac": None,
                        "network_name": "xe0"
                    },
                    "xe1": {
                        "local_ip": "192.168.100.132",
                        "local_mac": None,
                        "network_name": "xe1"
                    }
                },
                "ip": "192.168.100.132",
                "key_filename": "/tmp/yardstick_key-a3b663c2",
                "member-vnf-index": "3",
                "name": "vnf0us-k8syardstick-a3b663c2",
                "private_ip": "192.168.100.132",
                "service_ports": [
                    {
                        "name": "ssh",
                        "node_port": 57057,
                        "port": 22,
                        "protocol": "TCP",
                        "target_port": 22
                    },
                    {
                        "name": "lua",
                        "node_port": 29700,
                        "port": 22022,
                        "protocol": "TCP",
                        "target_port": 22022
                    }
                ],
                "ssh_port": 57057,
                "user": "root",
                "vnfd-id-ref": "vnf__0"
            },
            "vnf__1": {
                "VNF model": "../../vnf_descriptors/vnf_vcmts_tpl.yaml",
                "interfaces": {
                    "flannel": {
                        "local_ip": "192.168.100.134",
                        "local_mac": None,
                        "network_name": "flannel"
                    },
                    "xe0": {
                        "local_ip": "192.168.100.134",
                        "local_mac": None,
                        "network_name": "xe0"
                    },
                    "xe1": {
                        "local_ip": "192.168.100.134",
                        "local_mac": None,
                        "network_name": "xe1"
                    }
                },
                "ip": "192.168.100.134",
                "key_filename": "/tmp/yardstick_key-a3b663c2",
                "member-vnf-index": "4",
                "name": "vnf0ds-k8syardstick-a3b663c2",
                "private_ip": "192.168.100.134",
                "service_ports": [
                    {
                        "name": "ssh",
                        "node_port": 18581,
                        "port": 22,
                        "protocol": "TCP",
                        "target_port": 22
                    },
                    {
                        "name": "lua",
                        "node_port": 18469,
                        "port": 22022,
                        "protocol": "TCP",
                        "target_port": 22022
                    }
                ],
                "ssh_port": 18581,
                "user": "root",
                "vnfd-id-ref": "vnf__1"
            }
        }
    }

    PKTGEN_VALUES_PATH = "/tmp/pktgen_values.yaml"

    PKTGEN_VALUES = \
            "serviceAccount: cmk-serviceaccount\n" \
            "images:\n" \
            "  vcmts_pktgen: vcmts-pktgen:v18.10\n" \
            "topology:\n" \
            "  pktgen_replicas: 8\n" \
            "  pktgen_pods:\n" \
            "    - pktgen_id: 0\n" \
            "      num_ports: 4\n" \
            "      ports:\n" \
            "        - port_0:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.0\n" \
            "        - port_1:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.1\n" \
            "        - port_2:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.2\n" \
            "        - port_3:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.3\n" \
            "        - port_4:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.4\n" \
            "        - port_5:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.5\n" \
            "        - port_6:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.6\n" \
            "        - port_7:\n" \
            "          traffic_type: 'imix2'\n" \
            "          num_ofdm: 4\n" \
            "          num_subs: 300\n" \
            "          net_pktgen: 8a:02.7\n"

    def setUp(self):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.vcmts_pktgen = tg_vcmts_pktgen.VcmtsPktgen(NAME, vnfd)
        self.vcmts_pktgen._start_server = mock.Mock(return_value=0)
        self.vcmts_pktgen.resource_helper = mock.MagicMock()
        self.vcmts_pktgen.setup_helper = mock.MagicMock()

    def test___init__(self):
        self.assertFalse(self.vcmts_pktgen.traffic_finished)
        self.assertIsNotNone(self.vcmts_pktgen.setup_helper)
        self.assertIsNotNone(self.vcmts_pktgen.resource_helper)

    def test_extract_pod_cfg(self):
        pod_cfg = self.vcmts_pktgen.extract_pod_cfg(self.PKTGEN_POD_VALUES, "0")
        self.assertIsNotNone(pod_cfg)
        self.assertEqual(pod_cfg["pktgen_id"], "0")
        pod_cfg = self.vcmts_pktgen.extract_pod_cfg(self.PKTGEN_POD_VALUES, "4")
        self.assertIsNone(pod_cfg)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate_missing_pktgen_values_key(self, *args):
        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options'].pop('pktgen_values', None)
        with self.assertRaises(KeyError):
            self.vcmts_pktgen.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate_missing_pktgen_values_file(self, *args):
        if os.path.isfile(self.PKTGEN_VALUES_PATH):
            os.remove(self.PKTGEN_VALUES_PATH)
        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options']['pktgen_values'] = self.PKTGEN_VALUES_PATH
        with self.assertRaises(RuntimeError):
            self.vcmts_pktgen.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate_empty_pktgen_values_file(self, *args):
        yaml_sample = open(self.PKTGEN_VALUES_PATH, 'w')
        yaml_sample.write("")
        yaml_sample.close()

        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options']['pktgen_values'] = self.PKTGEN_VALUES_PATH
        with self.assertRaises(RuntimeError):
            self.vcmts_pktgen.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

        if os.path.isfile(self.PKTGEN_VALUES_PATH):
            os.remove(self.PKTGEN_VALUES_PATH)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate_invalid_pktgen_id(self, *args):
        yaml_sample = open(self.PKTGEN_VALUES_PATH, 'w')
        yaml_sample.write(self.PKTGEN_VALUES)
        yaml_sample.close()

        err_scenario_cfg = copy.deepcopy(self.SCENARIO_CFG)
        err_scenario_cfg['options'][NAME]['pktgen_id'] = 12
        with self.assertRaises(KeyError):
            self.vcmts_pktgen.instantiate(err_scenario_cfg, self.CONTEXT_CFG)

        if os.path.isfile(self.PKTGEN_VALUES_PATH):
            os.remove(self.PKTGEN_VALUES_PATH)

    @mock.patch.object(ctx_base.Context, 'get_context_from_server',
                       return_value='fake_context')
    def test_instantiate_all_valid(self, *args):
        yaml_sample = open(self.PKTGEN_VALUES_PATH, 'w')
        yaml_sample.write(self.PKTGEN_VALUES)
        yaml_sample.close()

        self.vcmts_pktgen.instantiate(self.SCENARIO_CFG, self.CONTEXT_CFG)
        self.assertIsNotNone(self.vcmts_pktgen.pod_cfg)
        self.assertEqual(self.vcmts_pktgen.pod_cfg["pktgen_id"], "0")

        if os.path.isfile(self.PKTGEN_VALUES_PATH):
            os.remove(self.PKTGEN_VALUES_PATH)

    def test_run_traffic_failed_connect(self):
        self.vcmts_pktgen.pktgen_helper = mock.MagicMock()
        self.vcmts_pktgen.pktgen_helper.connect.return_value = False
        with self.assertRaises(IOError):
            self.vcmts_pktgen.run_traffic({})

    def test_run_traffic_successful_connect(self):
        self.vcmts_pktgen.pktgen_helper = mock.MagicMock()
        self.vcmts_pktgen.pktgen_helper.connect.return_value = True
        self.vcmts_pktgen.pktgen_rate = 8.0
        self.assertTrue(self.vcmts_pktgen.run_traffic({}))
        self.vcmts_pktgen.pktgen_helper.connect.assert_called_once()
        self.vcmts_pktgen.pktgen_helper.send_command.assert_called_with(
            'pktgen.start("all");')
