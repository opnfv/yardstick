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
from multiprocessing import Process

import mock

from yardstick.benchmark.contexts import base as ctx_base
from yardstick.common import utils
from yardstick.network_services.helpers import cpu
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.vnf_generic.vnf import ipsec_vnf, vpp_helpers
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services.vnf_generic.vnf.ipsec_vnf import CryptoAlg, \
    IntegAlg, VipsecApproxSetupEnvHelper
from yardstick.tests.unit.network_services.vnf_generic.vnf.test_base import \
    mock_ssh

SSH_HELPER = 'yardstick.network_services.vnf_generic.vnf.sample_vnf.VnfSshHelper'

NAME = 'vnf__1'


class TestCryptoAlg(unittest.TestCase):

    def test__init__(self):
        encr_alg = CryptoAlg.AES_GCM_128
        self.assertEqual('aes-gcm-128', encr_alg.alg_name)
        self.assertEqual('AES-GCM', encr_alg.scapy_name)
        self.assertEqual(20, encr_alg.key_len)


class TestIntegAlg(unittest.TestCase):

    def test__init__(self):
        auth_alg = IntegAlg.AES_GCM_128
        self.assertEqual('aes-gcm-128', auth_alg.alg_name)
        self.assertEqual('AES-GCM', auth_alg.scapy_name)
        self.assertEqual(20, auth_alg.key_len)


@mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.Process")
class TestVipsecApproxVnf(unittest.TestCase):
    VNFD = {'vnfd:vnfd-catalog':
        {'vnfd':
            [{
                "benchmark": {
                    "kpi": [
                        "packets_in",
                        "packets_fwd",
                        "packets_dropped"
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
                "description": "VPP IPsec",
                "id": "VipsecApproxVnf",
                "mgmt-interface": {
                    "ip": "10.10.10.101",
                    "password": "r00t",
                    "user": "root",
                    "vdu-id": "ipsecvnf-baremetal"
                },
                "name": "IpsecVnf",
                "short-name": "IpsecVnf",
                "vdu": [
                    {
                        "description": "VPP Ipsec",
                        "external-interface": [
                            {
                                "name": "xe0",
                                "virtual-interface": {
                                    "dpdk_port_num": 0,
                                    "driver": "igb_uio",
                                    "dst_ip": "192.168.100.1",
                                    "dst_mac": "90:e2:ba:7c:30:e8",
                                    "ifname": "xe0",
                                    "local_ip": "192.168.100.2",
                                    "local_mac": "90:e2:ba:7c:41:a8",
                                    "netmask": "255.255.255.0",
                                    "network": {},
                                    "node_name": "vnf__0",
                                    "peer_ifname": "xe0",
                                    "peer_intf": {
                                        "dpdk_port_num": 0,
                                        "driver": "igb_uio",
                                        "dst_ip": "192.168.100.2",
                                        "dst_mac": "90:e2:ba:7c:41:a8",
                                        "ifname": "xe0",
                                        "local_ip": "192.168.100.1",
                                        "local_mac": "90:e2:ba:7c:30:e8",
                                        "netmask": "255.255.255.0",
                                        "network": {},
                                        "node_name": "tg__0",
                                        "peer_ifname": "xe0",
                                        "peer_name": "vnf__0",
                                        "vld_id": "uplink_0",
                                        "vpci": "0000:81:00.0"
                                    },
                                    "peer_name": "tg__0",
                                    "vld_id": "uplink_0",
                                    "vpci": "0000:ff:06.0"
                                },
                                "vnfd-connection-point-ref": "xe0"
                            },
                            {
                                "name": "xe1",
                                "virtual-interface": {
                                    "dpdk_port_num": 1,
                                    "driver": "igb_uio",
                                    "dst_ip": "1.1.1.2",
                                    "dst_mac": "0a:b1:ec:fd:a2:66",
                                    "ifname": "xe1",
                                    "local_ip": "1.1.1.1",
                                    "local_mac": "4e:90:85:d3:c5:13",
                                    "netmask": "255.255.255.0",
                                    "network": {},
                                    "node_name": "vnf__0",
                                    "peer_ifname": "xe1",
                                    "peer_intf": {
                                        "driver": "igb_uio",
                                        "dst_ip": "1.1.1.1",
                                        "dst_mac": "4e:90:85:d3:c5:13",
                                        "ifname": "xe1",
                                        "local_ip": "1.1.1.2",
                                        "local_mac": "0a:b1:ec:fd:a2:66",
                                        "netmask": "255.255.255.0",
                                        "network": {},
                                        "node_name": "vnf__1",
                                        "peer_ifname": "xe1",
                                        "peer_name": "vnf__0",
                                        "vld_id": "ciphertext",
                                        "vpci": "0000:00:07.0"
                                    },
                                    "peer_name": "vnf__1",
                                    "vld_id": "ciphertext",
                                    "vpci": "0000:ff:07.0"
                                },
                                "vnfd-connection-point-ref": "xe1"
                            }
                        ],
                        "id": "ipsecvnf-baremetal",
                        "name": "ipsecvnf-baremetal",
                        "routing_table": []
                    }
                ]
            }
            ]}}

    VNFD_ERROR = {'vnfd:vnfd-catalog':
        {'vnfd':
            [{
                "benchmark": {
                    "kpi": [
                        "packets_in",
                        "packets_fwd",
                        "packets_dropped"
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
                "description": "VPP IPsec",
                "id": "VipsecApproxVnf",
                "mgmt-interface": {
                    "ip": "10.10.10.101",
                    "password": "r00t",
                    "user": "root",
                    "vdu-id": "ipsecvnf-baremetal"
                },
                "name": "IpsecVnf",
                "short-name": "IpsecVnf",
                "vdu": [
                    {
                        "description": "VPP Ipsec",
                        "external-interface": [
                            {
                                "name": "xe0",
                                "virtual-interface": {
                                    "dpdk_port_num": 0,
                                    "driver": "igb_uio",
                                    "dst_ip": "192.168.100.1",
                                    "dst_mac": "90:e2:ba:7c:30:e8",
                                    "ifname": "xe0",
                                    "local_ip": "192.168.100.2",
                                    "local_mac": "90:e2:ba:7c:41:a8",
                                    "netmask": "255.255.255.0",
                                    "network": {},
                                    "node_name": "vnf__0",
                                    "peer_ifname": "xe0",
                                    "peer_intf": {
                                        "dpdk_port_num": 0,
                                        "driver": "igb_uio",
                                        "dst_ip": "192.168.100.2",
                                        "dst_mac": "90:e2:ba:7c:41:a8",
                                        "ifname": "xe0",
                                        "local_ip": "192.168.100.1",
                                        "local_mac": "90:e2:ba:7c:30:e8",
                                        "netmask": "255.255.255.0",
                                        "network": {},
                                        "node_name": "tg__0",
                                        "peer_ifname": "xe0",
                                        "peer_name": "vnf__0",
                                        "vld_id": "uplink_0",
                                        "vpci": "0000:81:00.0"
                                    },
                                    "peer_name": "tg__0",
                                    "vld_id": "uplink_1",
                                    "vpci": "0000:ff:06.0"
                                },
                                "vnfd-connection-point-ref": "xe0"
                            },
                            {
                                "name": "xe1",
                                "virtual-interface": {
                                    "dpdk_port_num": 1,
                                    "driver": "igb_uio",
                                    "dst_ip": "1.1.1.2",
                                    "dst_mac": "0a:b1:ec:fd:a2:66",
                                    "ifname": "xe1",
                                    "local_ip": "1.1.1.1",
                                    "local_mac": "4e:90:85:d3:c5:13",
                                    "netmask": "255.255.255.0",
                                    "network": {},
                                    "node_name": "vnf__1",
                                    "peer_ifname": "xe1",
                                    "peer_intf": {
                                        "driver": "igb_uio",
                                        "dst_ip": "1.1.1.1",
                                        "dst_mac": "4e:90:85:d3:c5:13",
                                        "ifname": "xe1",
                                        "local_ip": "1.1.1.2",
                                        "local_mac": "0a:b1:ec:fd:a2:66",
                                        "netmask": "255.255.255.0",
                                        "network": {},
                                        "node_name": "vnf__1",
                                        "peer_ifname": "xe1",
                                        "peer_name": "vnf__0",
                                        "vld_id": "ciphertext",
                                        "vpci": "0000:00:07.0"
                                    },
                                    "peer_name": "vnf__1",
                                    "vld_id": "ciphertext",
                                    "vpci": "0000:ff:07.0"
                                },
                                "vnfd-connection-point-ref": "xe1"
                            }
                        ],
                        "id": "ipsecvnf-baremetal",
                        "name": "ipsecvnf-baremetal",
                        "routing_table": []
                    }
                ]
            }
            ]}}

    scenario_cfg = {
        "nodes": {
            "tg__0": "trafficgen.yardstick-5486cc2f",
            "vnf__0": "vnf0.yardstick-5486cc2f",
            "vnf__1": "vnf1.yardstick-5486cc2f"
        },
        "options": {
            "flow": {
                "count": 1,
                "dst_ip": [
                    "20.0.0.0-20.0.0.100"
                ],
                "src_ip": [
                    "10.0.0.0-10.0.0.100"
                ]
            },
            "framesize": {
                "downlink": {
                    "64B": 100
                },
                "uplink": {
                    "64B": 100
                }
            },
            "rfc2544": {
                "allowed_drop_rate": "0.0 - 0.005"
            },
            "tg__0": {
                "collectd": {
                    "interval": 1
                },
                "queues_per_port": 7
            },
            "traffic_type": 4,
            "vnf__0": {
                "collectd": {
                    "interval": 1
                },
                "vnf_config": {
                    "crypto_type": "SW_cryptodev",
                    "rxq": 1,
                    "worker_config": "1C/1T",
                    "worker_threads": 4
                }
            },
            "vnf__1": {
                "collectd": {
                    "interval": 1
                },
                "vnf_config": {
                    "crypto_type": "SW_cryptodev",
                    "rxq": 1,
                    "worker_config": "1C/1T",
                    "worker_threads": 4
                }
            },
            "vpp_config": {
                "crypto_algorithms": "aes-gcm",
                "tunnel": 1
            }
        },
        "runner": {
            "duration": 500,
            "interval": 10,
            "object":
                "yardstick.benchmark.scenarios.networking.vnf_generic.NetworkServiceTestCase",
            "output_config": {
                "DEFAULT": {
                    "debug": "False",
                    "dispatcher": [
                        "influxdb"
                    ]
                },
                "dispatcher_file": {
                    "debug": "False",
                    "dispatcher": "influxdb",
                    "file_path": "/tmp/yardstick.out"
                },
                "dispatcher_http": {
                    "debug": "False",
                    "dispatcher": "influxdb",
                    "target": "http://127.0.0.1:8000/results",
                    "timeout": "20"
                },
                "dispatcher_influxdb": {
                    "db_name": "yardstick",
                    "debug": "False",
                    "dispatcher": "influxdb",
                    "password": "r00t",
                    "target": "http://192.168.100.3:8086",
                    "timeout": "20",
                    "username": "root"
                },
                "nsb": {
                    "bin_path": "/opt/nsb_bin",
                    "debug": "False",
                    "dispatcher": "influxdb",
                    "trex_client_lib": "/opt/nsb_bin/trex_client/stl",
                    "trex_path": "/opt/nsb_bin/trex/scripts"
                }
            },
            "runner_id": 1105,
            "type": "Duration"
        },
        "task_id": "5486cc2f-d4d3-4feb-b0df-5e0bcd584c9e",
        "task_path": "samples/vnf_samples/nsut/ipsec",
        "tc": "tc_baremetal_rfc2544_ipv4_1flow_sw_aesgcm_4cores_64B_trex",
        "topology": "vpp-tg-topology-2.yaml",
        "traffic_profile": "../../traffic_profiles/ipv4_throughput_latency_vpp.yaml",
        "type": "NSPerf"
    }

    context_cfg = {
        "networks": {},
        "nodes": {
            "tg__0": {
                "VNF model": "../../vnf_descriptors/tg_vpp_tpl.yaml",
                "ctx_type": "Node",
                "interfaces": {
                    "xe0": {
                        "dpdk_port_num": 0,
                        "driver": "igb_uio",
                        "dst_ip": "192.168.100.2",
                        "dst_mac": "90:e2:ba:7c:41:a8",
                        "ifname": "xe0",
                        "local_ip": "192.168.100.1",
                        "local_mac": "90:e2:ba:7c:30:e8",
                        "netmask": "255.255.255.0",
                        "network": {},
                        "node_name": "tg__0",
                        "peer_ifname": "xe0",
                        "peer_intf": {
                            "dpdk_port_num": 0,
                            "driver": "igb_uio",
                            "dst_ip": "192.168.100.1",
                            "dst_mac": "90:e2:ba:7c:30:e8",
                            "ifname": "xe0",
                            "local_ip": "192.168.100.2",
                            "local_mac": "90:e2:ba:7c:41:a8",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "vnf__0",
                            "peer_ifname": "xe0",
                            "peer_name": "tg__0",
                            "vld_id": "uplink_0",
                            "vpci": "0000:00:06.0"
                        },
                        "peer_name": "vnf__0",
                        "vld_id": "uplink_0",
                        "vpci": "0000:81:00.0"
                    },
                    "xe1": {
                        "dpdk_port_num": 1,
                        "driver": "igb_uio",
                        "dst_ip": "192.168.101.2",
                        "dst_mac": "90:e2:ba:7c:41:a9",
                        "ifname": "xe1",
                        "local_ip": "192.168.101.1",
                        "local_mac": "90:e2:ba:7c:30:e9",
                        "netmask": "255.255.255.0",
                        "network": {},
                        "node_name": "tg__0",
                        "peer_ifname": "xe0",
                        "peer_intf": {
                            "dpdk_port_num": 1,
                            "driver": "igb_uio",
                            "dst_ip": "192.168.101.1",
                            "dst_mac": "90:e2:ba:7c:30:e9",
                            "ifname": "xe0",
                            "local_ip": "192.168.101.2",
                            "local_mac": "90:e2:ba:7c:41:a9",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "vnf__1",
                            "peer_ifname": "xe1",
                            "peer_name": "tg__0",
                            "vld_id": "downlink_0",
                            "vpci": "0000:00:06.0"
                        },
                        "peer_name": "vnf__1",
                        "vld_id": "downlink_0",
                        "vpci": "0000:81:00.1"
                    }
                },
                "ip": "10.10.10.10",
                "member-vnf-index": "1",
                "name": "trafficgen.yardstick-5486cc2f",
                "password": "r00t",
                "port": 22,
                "role": "TrafficGen",
                "user": "root",
                "username": "root",
                "vnfd-id-ref": "tg__0"
            },
            "vnf__0": {
                "VNF model": "../../vnf_descriptors/vpp_vnfd.yaml",
                "ctx_type": "Node",
                "interfaces": {
                    "xe0": {
                        "dpdk_port_num": 0,
                        "driver": "igb_uio",
                        "dst_ip": "192.168.100.1",
                        "dst_mac": "90:e2:ba:7c:30:e8",
                        "ifname": "xe0",
                        "local_ip": "192.168.100.2",
                        "local_mac": "90:e2:ba:7c:41:a8",
                        "netmask": "255.255.255.0",
                        "network": {},
                        "node_name": "vnf__0",
                        "peer_ifname": "xe0",
                        "peer_intf": {
                            "dpdk_port_num": 0,
                            "driver": "igb_uio",
                            "dst_ip": "192.168.100.2",
                            "dst_mac": "90:e2:ba:7c:41:a8",
                            "ifname": "xe0",
                            "local_ip": "192.168.100.1",
                            "local_mac": "90:e2:ba:7c:30:e8",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "tg__0",
                            "peer_ifname": "xe0",
                            "peer_name": "vnf__0",
                            "vld_id": "uplink_0",
                            "vpci": "0000:81:00.0"
                        },
                        "peer_name": "tg__0",
                        "vld_id": "uplink_0",
                        "vpci": "0000:00:06.0"
                    },
                    "xe1": {
                        "dpdk_port_num": 1,
                        "driver": "igb_uio",
                        "dst_ip": "1.1.1.2",
                        "dst_mac": "0a:b1:ec:fd:a2:66",
                        "ifname": "xe1",
                        "local_ip": "1.1.1.1",
                        "local_mac": "4e:90:85:d3:c5:13",
                        "netmask": "255.255.255.0",
                        "network": {},
                        "node_name": "vnf__0",
                        "peer_ifname": "xe1",
                        "peer_intf": {
                            "dpdk_port_num": 1,
                            "driver": "igb_uio",
                            "dst_ip": "1.1.1.1",
                            "dst_mac": "4e:90:85:d3:c5:13",
                            "ifname": "xe1",
                            "local_ip": "1.1.1.2",
                            "local_mac": "0a:b1:ec:fd:a2:66",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "vnf__1",
                            "peer_ifname": "xe1",
                            "peer_name": "vnf__0",
                            "vld_id": "ciphertext",
                            "vpci": "0000:00:07.0"
                        },
                        "peer_name": "vnf__1",
                        "vld_id": "ciphertext",
                        "vpci": "0000:00:07.0"
                    }
                },
                "ip": "10.10.10.101",
                "member-vnf-index": "2",
                "name": "vnf0.yardstick-5486cc2f",
                "password": "r00t",
                "port": 22,
                "role": "VirtualNetworkFunction",
                "user": "root",
                "username": "root",
                "vnfd-id-ref": "vnf__0"
            },
            "vnf__1": {
                "VNF model": "../../vnf_descriptors/vpp_vnfd.yaml",
                "ctx_type": "Node",
                "interfaces": {
                    "xe0": {
                        "dpdk_port_num": 0,
                        "driver": "igb_uio",
                        "dst_ip": "192.168.101.1",
                        "dst_mac": "90:e2:ba:7c:30:e9",
                        "ifname": "xe0",
                        "local_ip": "192.168.101.2",
                        "local_mac": "90:e2:ba:7c:41:a9",
                        "netmask": "255.255.255.0",
                        "network": {},
                        "node_name": "vnf__1",
                        "peer_ifname": "xe1",
                        "peer_intf": {
                            "dpdk_port_num": 1,
                            "driver": "igb_uio",
                            "dst_ip": "192.168.101.2",
                            "dst_mac": "90:e2:ba:7c:41:a9",
                            "ifname": "xe1",
                            "local_ip": "192.168.101.1",
                            "local_mac": "90:e2:ba:7c:30:e9",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "tg__0",
                            "peer_ifname": "xe0",
                            "peer_name": "vnf__1",
                            "vld_id": "downlink_0",
                            "vpci": "0000:81:00.1"
                        },
                        "peer_name": "tg__0",
                        "vld_id": "downlink_0",
                        "vpci": "0000:00:06.0"
                    },
                    "xe1": {
                        "dpdk_port_num": 1,
                        "driver": "igb_uio",
                        "dst_ip": "1.1.1.1",
                        "dst_mac": "4e:90:85:d3:c5:13",
                        "ifname": "xe1",
                        "local_ip": "1.1.1.2",
                        "local_mac": "0a:b1:ec:fd:a2:66",
                        "netmask": "255.255.255.0",
                        "network": {},
                        "node_name": "vnf__1",
                        "peer_ifname": "xe1",
                        "peer_intf": {
                            "dpdk_port_num": 1,
                            "driver": "igb_uio",
                            "dst_ip": "1.1.1.2",
                            "dst_mac": "0a:b1:ec:fd:a2:66",
                            "ifname": "xe1",
                            "local_ip": "1.1.1.1",
                            "local_mac": "4e:90:85:d3:c5:13",
                            "netmask": "255.255.255.0",
                            "network": {},
                            "node_name": "vnf__0",
                            "peer_ifname": "xe1",
                            "peer_name": "vnf__1",
                            "vld_id": "ciphertext",
                            "vpci": "0000:00:07.0"
                        },
                        "peer_name": "vnf__0",
                        "vld_id": "ciphertext",
                        "vpci": "0000:00:07.0"
                    }
                },
                "ip": "10.10.10.102",
                "member-vnf-index": "3",
                "name": "vnf1.yardstick-5486cc2f",
                "password": "r00t",
                "port": 22,
                "role": "VirtualNetworkFunction",
                "user": "root",
                "username": "root",
                "vnfd-id-ref": "vnf__1"
            }
        }
    }

    def test___init__(self, *args):
        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        self.assertIsNone(vipsec_vnf._vnf_process)

    @mock.patch(SSH_HELPER)
    def test__run(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        vipsec_vnf._build_config = mock.MagicMock()
        vipsec_vnf.setup_helper.kill_vnf = mock.MagicMock()
        vipsec_vnf.setup_helper.create_ipsec_tunnels = mock.MagicMock()
        vipsec_vnf.queue_wrapper = mock.MagicMock()
        vipsec_vnf.scenario_helper.scenario_cfg = self.scenario_cfg
        vipsec_vnf.vnf_cfg = {'lb_config': 'SW',
                              'lb_count': 1,
                              'worker_config': '1C/1T',
                              'worker_threads': 1}
        vipsec_vnf.all_options = {'traffic_type': '4',
                                  'topology': 'nsb_test_case.yaml'}
        vipsec_vnf._run()
        # vipsec_vnf.setup_helper.ssh_helper.execute.assert_called_once()

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate(self, ssh, *args):
        mock_ssh(ssh)

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = True
        mock_process.exitcode = 432

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        vipsec_vnf.resource_helper.resource = mock.MagicMock()
        vipsec_vnf.setup_helper = mock.MagicMock()
        vipsec_vnf.setup_helper.check_status.return_value = True
        vipsec_vnf._vnf_process = mock_process
        vipsec_vnf.WAIT_TIME = 0
        self.assertEqual(vipsec_vnf.wait_for_instantiate(), 432)

    @mock.patch(SSH_HELPER)
    def test_wait_for_instantiate_crash(self, ssh, *args):
        mock_ssh(ssh)

        mock_process = mock.Mock(autospec=Process)
        mock_process.is_alive.return_value = False
        mock_process.exitcode = 432

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        vipsec_vnf.resource_helper.resource = mock.MagicMock()
        vipsec_vnf.setup_helper = mock.MagicMock()
        vipsec_vnf.setup_helper.check_status.return_value = False
        vipsec_vnf._vnf_process = mock_process
        vipsec_vnf.WAIT_TIME = 0
        vipsec_vnf.WAIT_TIME_FOR_SCRIPT = 0

        with self.assertRaises(RuntimeError) as raised:
            vipsec_vnf.wait_for_instantiate()

        self.assertIn('VNF process died', str(raised.exception))

    @mock.patch.object(ctx_base.Context, 'get_physical_node_from_server',
                       return_value='mock_node')
    @mock.patch.object(ipsec_vnf.VipsecApproxSetupEnvHelper,
                       'get_vpp_statistics',
                       return_value={'packets_in': 0, 'packets_fwd': 0,
                                     'packets_dropped': 0})
    @mock.patch(SSH_HELPER)
    def test_collect_kpi(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        vipsec_vnf.scenario_helper.scenario_cfg = {
            'nodes': {vipsec_vnf.name: "mock"}
        }
        result = {
            'collect_stats': {'packets_in': 0, 'packets_fwd': 0,
                              'packets_dropped': 0},
            'physical_node': 'mock_node'
        }
        self.assertEqual(result, vipsec_vnf.collect_kpi())

    @mock.patch.object(utils, 'find_relative_file')
    @mock.patch(
        "yardstick.network_services.vnf_generic.vnf.sample_vnf.Context")
    @mock.patch(SSH_HELPER)
    def test_instantiate(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        vipsec_vnf.deploy_helper = mock.MagicMock()
        vipsec_vnf.resource_helper = mock.MagicMock()
        vipsec_vnf._build_config = mock.MagicMock()
        vipsec_vnf.WAIT_TIME = 0
        self.scenario_cfg.update({"nodes": {"vnf__1": ""}})
        self.assertIsNone(vipsec_vnf.instantiate(self.scenario_cfg,
                                                 self.context_cfg))

    @mock.patch.object(ipsec_vnf.VipsecApproxSetupEnvHelper, 'kill_vnf',
                       return_value='')
    @mock.patch("yardstick.network_services.vnf_generic.vnf.sample_vnf.time")
    @mock.patch(SSH_HELPER)
    def test_terminate(self, ssh, *args):
        mock_ssh(ssh)

        vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        vipsec_vnf = ipsec_vnf.VipsecApproxVnf(NAME, vnfd)
        vipsec_vnf._vnf_process = mock.MagicMock()
        vipsec_vnf._vnf_process.terminate = mock.Mock()
        self.assertIsNone(vipsec_vnf.terminate())


class TestVipsecApproxSetupEnvHelper(unittest.TestCase):
    ALL_OPTIONS = {
        "flow": {
            "count": 1,
            "dst_ip": [
                "20.0.0.0-20.0.0.100"
            ],
            "src_ip": [
                "10.0.0.0-10.0.0.100"
            ]
        },
        "framesize": {
            "downlink": {
                "64B": 100
            },
            "uplink": {
                "64B": 100
            }
        },
        "rfc2544": {
            "allowed_drop_rate": "0.0 - 0.005"
        },
        "tg__0": {
            "collectd": {
                "interval": 1
            },
            "queues_per_port": 7
        },
        "traffic_type": 4,
        "vnf__0": {
            "collectd": {
                "interval": 1
            },
            "vnf_config": {
                "crypto_type": "SW_cryptodev",
                "rxq": 1,
                "worker_config": "1C/1T",
                "worker_threads": 4
            }
        },
        "vnf__1": {
            "collectd": {
                "interval": 1
            },
            "vnf_config": {
                "crypto_type": "SW_cryptodev",
                "rxq": 1,
                "worker_config": "1C/1T",
                "worker_threads": 4
            }
        },
        "vpp_config": {
            "crypto_algorithms": "aes-gcm",
            "tunnel": 1
        }
    }

    ALL_OPTIONS_CBC_ALGORITHMS = {
        "flow": {
            "count": 1,
            "dst_ip": [
                "20.0.0.0-20.0.0.100"
            ],
            "src_ip": [
                "10.0.0.0-10.0.0.100"
            ]
        },
        "framesize": {
            "downlink": {
                "64B": 100
            },
            "uplink": {
                "64B": 100
            }
        },
        "rfc2544": {
            "allowed_drop_rate": "0.0 - 0.005"
        },
        "tg__0": {
            "collectd": {
                "interval": 1
            },
            "queues_per_port": 7
        },
        "traffic_type": 4,
        "vnf__0": {
            "collectd": {
                "interval": 1
            },
            "vnf_config": {
                "crypto_type": "SW_cryptodev",
                "rxq": 1,
                "worker_config": "1C/1T",
                "worker_threads": 4
            }
        },
        "vnf__1": {
            "collectd": {
                "interval": 1
            },
            "vnf_config": {
                "crypto_type": "SW_cryptodev",
                "rxq": 1,
                "worker_config": "1C/1T",
                "worker_threads": 4
            }
        },
        "vpp_config": {
            "crypto_algorithms": "cbc-sha1",
            "tunnel": 1
        }
    }

    ALL_OPTIONS_ERROR = {
        "flow_error": {
            "count": 1,
            "dst_ip": [
                "20.0.0.0-20.0.0.100"
            ],
            "src_ip": [
                "10.0.0.0-10.0.0.100"
            ]
        },
        "framesize": {
            "downlink": {
                "64B": 100
            },
            "uplink": {
                "64B": 100
            }
        },
        "rfc2544": {
            "allowed_drop_rate": "0.0 - 0.005"
        },
        "tg__0": {
            "collectd": {
                "interval": 1
            },
            "queues_per_port": 7
        },
        "traffic_type": 4,
        "vnf__0": {
            "collectd": {
                "interval": 1
            },
            "vnf_config": {
                "crypto_type": "SW_cryptodev",
                "rxq": 1,
                "worker_config": "1C/1T",
                "worker_threads": 4
            }
        },
        "vnf__1": {
            "collectd": {
                "interval": 1
            },
            "vnf_config": {
                "crypto_type": "SW_cryptodev",
                "rxq": 1,
                "worker_config": "1C/1T",
                "worker_threads": 4
            }
        },
        "vpp_config": {
            "crypto_algorithms": "aes-gcm",
            "tunnel": 1
        }
    }

    OPTIONS = {
        "collectd": {
            "interval": 1
        },
        "vnf_config": {
            "crypto_type": "SW_cryptodev",
            "rxq": 1,
            "worker_config": "1C/1T",
            "worker_threads": 4
        }
    }

    OPTIONS_HW = {
        "collectd": {
            "interval": 1
        },
        "vnf_config": {
            "crypto_type": "HW_cryptodev",
            "rxq": 1,
            "worker_config": "1C/1T",
            "worker_threads": 4
        }
    }

    CPU_LAYOUT = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0],
                              [1, 0, 0, 0, 0, 1, 1, 0],
                              [2, 1, 0, 0, 0, 2, 2, 1],
                              [3, 1, 0, 0, 0, 3, 3, 1],
                              [4, 2, 0, 0, 0, 4, 4, 2],
                              [5, 2, 0, 0, 0, 5, 5, 2],
                              [6, 3, 0, 0, 0, 6, 6, 3],
                              [7, 3, 0, 0, 0, 7, 7, 3],
                              [8, 4, 0, 0, 0, 8, 8, 4],
                              [9, 5, 0, 1, 0, 9, 9, 4],
                              [10, 6, 0, 1, 0, 10, 10, 5],
                              [11, 6, 0, 1, 0, 11, 11, 5],
                              [12, 7, 0, 1, 0, 12, 12, 6],
                              [13, 7, 0, 1, 0, 13, 13, 6],
                              [14, 8, 0, 1, 0, 14, 14, 7],
                              [15, 8, 0, 1, 0, 15, 15, 7],
                              [16, 9, 0, 1, 0, 16, 16, 8],
                              [17, 9, 0, 1, 0, 17, 17, 8]]}
    CPU_SMT = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0],
                           [1, 0, 0, 0, 0, 1, 1, 0],
                           [2, 1, 0, 0, 0, 2, 2, 1],
                           [3, 1, 0, 0, 0, 3, 3, 1],
                           [4, 2, 0, 0, 0, 4, 4, 2],
                           [5, 2, 0, 0, 0, 5, 5, 2],
                           [6, 3, 0, 0, 0, 6, 6, 3],
                           [7, 3, 0, 0, 0, 7, 7, 3],
                           [8, 4, 0, 0, 0, 8, 8, 4],
                           [9, 5, 0, 1, 0, 0, 0, 0],
                           [10, 6, 0, 1, 0, 1, 1, 0],
                           [11, 6, 0, 1, 0, 2, 2, 1],
                           [12, 7, 0, 1, 0, 3, 3, 1],
                           [13, 7, 0, 1, 0, 4, 4, 2],
                           [14, 8, 0, 1, 0, 5, 5, 2],
                           [15, 8, 0, 1, 0, 6, 6, 3],
                           [16, 9, 0, 1, 0, 7, 7, 3],
                           [17, 9, 0, 1, 0, 8, 8, 4]]}

    VPP_INTERFACES_DUMP = [
        {
            "sw_if_index": 0,
            "sup_sw_if_index": 0,
            "l2_address_length": 0,
            "l2_address": [0, 0, 0, 0, 0, 0, 0, 0],
            "interface_name": "local0",
            "admin_up_down": 0,
            "link_up_down": 0,
            "link_duplex": 0,
            "link_speed": 0,
            "mtu": 0,
            "sub_id": 0,
            "sub_dot1ad": 0,
            "sub_number_of_tags": 0,
            "sub_outer_vlan_id": 0,
            "sub_inner_vlan_id": 0,
            "sub_exact_match": 0,
            "sub_default": 0,
            "sub_outer_vlan_id_any": 0,
            "sub_inner_vlan_id_any": 0,
            "vtr_op": 0,
            "vtr_push_dot1q": 0,
            "vtr_tag1": 0,
            "vtr_tag2": 0
        },
        {
            "sw_if_index": 1,
            "sup_sw_if_index": 1,
            "l2_address_length": 6,
            "l2_address": [144, 226, 186, 124, 65, 168, 0, 0],
            "interface_name": "TenGigabitEthernetff/6/0",
            "admin_up_down": 0,
            "link_up_down": 0,
            "link_duplex": 2,
            "link_speed": 32,
            "mtu": 9202,
            "sub_id": 0,
            "sub_dot1ad": 0,
            "sub_number_of_tags": 0,
            "sub_outer_vlan_id": 0,
            "sub_inner_vlan_id": 0,
            "sub_exact_match": 0,
            "sub_default": 0,
            "sub_outer_vlan_id_any": 0,
            "sub_inner_vlan_id_any": 0,
            "vtr_op": 0,
            "vtr_push_dot1q": 0,
            "vtr_tag1": 0,
            "vtr_tag2": 0
        },
        {
            "sw_if_index": 2,
            "sup_sw_if_index": 2,
            "l2_address_length": 6,
            "l2_address": [78, 144, 133, 211, 197, 19, 0, 0],
            "interface_name": "VirtualFunctionEthernetff/7/0",
            "admin_up_down": 0,
            "link_up_down": 0,
            "link_duplex": 2,
            "link_speed": 32,
            "mtu": 9206,
            "sub_id": 0,
            "sub_dot1ad": 0,
            "sub_number_of_tags": 0,
            "sub_outer_vlan_id": 0,
            "sub_inner_vlan_id": 0,
            "sub_exact_match": 0,
            "sub_default": 0,
            "sub_outer_vlan_id_any": 0,
            "sub_inner_vlan_id_any": 0,
            "vtr_op": 0,
            "vtr_push_dot1q": 0,
            "vtr_tag1": 0,
            "vtr_tag2": 0
        }
    ]

    VPP_INTERFACES_STATUS = \
        '              Name               Idx    State  MTU (L3/IP4/IP6/MPLS)' \
        'Counter          Count     \n' \
        'TenGigabitEthernetff/6/0          1     up         9000/0/0/0    \n' \
        'VirtualFunctionEthernetff/7/0     2     up         9000/0/0/0    \n' \
        'ipsec0                            2     up         9000/0/0/0    \n' \
        'local0                            0     down          0/0/0/0      '

    VPP_INTERFACES_STATUS_FALSE = \
        '              Name               Idx    State  MTU (L3/IP4/IP6/MPLS)' \
        'Counter          Count     \n' \
        'TenGigabitEthernetff/6/0          1     down         9000/0/0/0  \n' \
        'VirtualFunctionEthernetff/7/0     2     down         9000/0/0/0  \n' \
        'ipsec0                            2     down         9000/0/0/0  \n' \
        'local0                            0     down          0/0/0/0      '

    def test__get_crypto_type(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual('SW_cryptodev',
                         ipsec_approx_setup_helper._get_crypto_type())

    def test__get_crypto_algorithms(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual('aes-gcm',
                         ipsec_approx_setup_helper._get_crypto_algorithms())

    def test__get_n_tunnels(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(1, ipsec_approx_setup_helper._get_n_tunnels())

    def test__get_n_connections(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(1, ipsec_approx_setup_helper._get_n_connections())

    def test__get_n_connections_error(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS_ERROR

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        with self.assertRaises(KeyError) as raised:
            ipsec_approx_setup_helper._get_n_connections()
        self.assertIn(
            'Missing flow definition in scenario section of the task definition file',
            str(raised.exception))

    def test__get_flow_src_start_ip(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual('10.0.0.0',
                         ipsec_approx_setup_helper._get_flow_src_start_ip())

    def test__get_flow_src_start_ip_vnf1(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD_ERROR['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual('20.0.0.0',
                         ipsec_approx_setup_helper._get_flow_src_start_ip())

    def test__get_flow_src_start_ip_error(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS_ERROR

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        with self.assertRaises(KeyError) as raised:
            ipsec_approx_setup_helper._get_flow_src_start_ip()
        self.assertIn(
            'Missing flow definition in scenario section of the task definition file',
            str(raised.exception))

    def test__get_flow_dst_start_ip(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual('20.0.0.0',
                         ipsec_approx_setup_helper._get_flow_dst_start_ip())

    def test__get_flow_dst_start_ip_vnf1(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD_ERROR['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual('10.0.0.0',
                         ipsec_approx_setup_helper._get_flow_dst_start_ip())

    def test__get_flow_dst_start_ip_error(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        scenario_helper.all_options = self.ALL_OPTIONS_ERROR

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        with self.assertRaises(KeyError) as raised:
            ipsec_approx_setup_helper._get_flow_dst_start_ip()
        self.assertIn(
            'Missing flow definition in scenario section of the task definition file',
            str(raised.exception))

    def test_build_config(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
            self.assertIsNone(ipsec_approx_setup_helper.build_config())
        self.assertEqual(0,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'numa_node'))
        self.assertEqual('TenGigabitEthernetff/6/0',
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'vpp_name'))
        self.assertEqual(1,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'vpp_sw_index'))
        self.assertEqual(0,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'numa_node'))
        self.assertEqual('VirtualFunctionEthernetff/7/0',
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'vpp_name'))
        self.assertEqual(2,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'vpp_sw_index'))
        self.assertGreaterEqual(ssh_helper.execute.call_count, 4)

    def test_build_config_cbc_algorithms(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS_CBC_ALGORITHMS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
            self.assertIsNone(ipsec_approx_setup_helper.build_config())
        self.assertEqual(0,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'numa_node'))
        self.assertEqual('TenGigabitEthernetff/6/0',
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'vpp_name'))
        self.assertEqual(1,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'vpp_sw_index'))
        self.assertEqual(0,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'numa_node'))
        self.assertEqual('VirtualFunctionEthernetff/7/0',
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'vpp_name'))
        self.assertEqual(2,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'vpp_sw_index'))
        self.assertGreaterEqual(ssh_helper.execute.call_count, 4)

    @mock.patch.object(utils, 'setup_hugepages')
    def test_setup_vnf_environment(self, *args):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.nodes = [None, None]
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            self.assertIsInstance(
                ipsec_approx_setup_helper.setup_vnf_environment(),
                ResourceProfile)
        self.assertEqual(0,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'numa_node'))
        self.assertEqual('TenGigabitEthernetff/6/0',
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'vpp_name'))
        self.assertEqual(1,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe0', 'vpp_sw_index'))
        self.assertEqual(0,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'numa_node'))
        self.assertEqual('VirtualFunctionEthernetff/7/0',
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'vpp_name'))
        self.assertEqual(2,
                         ipsec_approx_setup_helper.get_value_by_interface_key(
                             'xe1', 'vpp_sw_index'))
        self.assertGreaterEqual(ssh_helper.execute.call_count, 4)

    def test_calculate_frame_size(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(16984 / 48,
                         ipsec_approx_setup_helper.calculate_frame_size(
                             {'64B': 28, '570B': 16, '1518B': 4}))

    def test_calculate_frame_size_64(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(64,
                         ipsec_approx_setup_helper.calculate_frame_size({}))

    def test_calculate_frame_size_64_error(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(64,
                         ipsec_approx_setup_helper.calculate_frame_size(
                             {'64B': -28, '570B': 16, '1518B': 4}))

    def test_check_status(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, self.VPP_INTERFACES_STATUS, ''
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertTrue(ipsec_approx_setup_helper.check_status())

    def test_check_status_false(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, self.VPP_INTERFACES_STATUS_FALSE, ''
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertFalse(ipsec_approx_setup_helper.check_status())

    def test_get_vpp_statistics(self):
        def execute(cmd):
            if 'TenGigabitEthernetff/6/0' in cmd:
                return 0, output_xe0, ''
            elif 'VirtualFunctionEthernetff/7/0' in cmd:
                return 0, output_xe1, ''
            return 0, '0', ''

        output_xe0 = \
            '              Name               Idx    State  MTU (L3/IP4/IP6/MPLS)' \
            '     Counter          Count     \n' \
            'TenGigabitEthernetff/6/0          1      up          9200/0/0/0     ' \
            'rx packets              23373568\n' \
            '                                                                    ' \
            'rx bytes              1402414080\n' \
            '                                                                    ' \
            'tx packets              20476416\n' \
            '                                                                    ' \
            'tx bytes              1228584960\n' \
            '                                                                    ' \
            'ip4                     23373568\n' \
            '                                                                    ' \
            'rx-miss                 27789925'
        output_xe1 = \
            '              Name               Idx    State  MTU (L3/IP4/IP6/MPLS)' \
            '     Counter          Count     \n' \
            'VirtualFunctionEthernetff/7/0     2      up          9200/0/0/0     ' \
            'rx packets              23373568\n' \
            '                                                                    ' \
            'rx bytes              1402414080\n' \
            '                                                                    ' \
            'tx packets              20476416\n' \
            '                                                                    ' \
            'tx bytes              1228584960\n' \
            '                                                                    ' \
            'ip4                     23373568\n' \
            '                                                                    ' \
            'rx-miss                 27789925'

        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute = execute
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertEqual({'xe0': {'packets_dropped': 27789925,
                                  'packets_fwd': 20476416,
                                  'packets_in': 23373568},
                          'xe1': {'packets_dropped': 27789925,
                                  'packets_fwd': 20476416,
                                  'packets_in': 23373568}},
                         ipsec_approx_setup_helper.get_vpp_statistics())

    def test_parser_vpp_stats(self):
        output = \
            '         Name               Idx    State  MTU (L3/IP4/IP6/MPLS)' \
            'Counter          Count     \n' \
            'TenGigabitEthernetff/6/0          1      up        9200/0/0/0  ' \
            'rx packets              23373568\n' \
            '                                                               ' \
            'rx bytes              1402414080\n' \
            '                                                               ' \
            'tx packets              20476416\n' \
            '                                                               ' \
            'tx bytes              1228584960\n' \
            '                                                               ' \
            'ip4                     23373568\n' \
            '                                                               ' \
            'rx-miss                 27789925'
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual({'xe0': {'packets_dropped': 27789925,
                                  'packets_fwd': 20476416,
                                  'packets_in': 23373568}},
                         ipsec_approx_setup_helper.parser_vpp_stats('xe0',
                                                                    'TenGigabitEthernetff/6/0',
                                                                    output))

    def test_parser_vpp_stats_no_miss(self):
        output = \
            '              Name               Idx    State              ' \
            'Counter          Count     \n' \
            'TenGigabitEthernetff/6/0          1      up                ' \
            'rx packets              23373568\n' \
            '                                                           ' \
            'rx bytes              1402414080\n' \
            '                                                           ' \
            'tx packets              20476416\n' \
            '                                                           ' \
            'tx bytes              1228584960\n' \
            '                                                           ' \
            'ip4                     23373568'
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual({'xe0': {'packets_dropped': 2897152,
                                  'packets_fwd': 20476416,
                                  'packets_in': 23373568}},
                         ipsec_approx_setup_helper.parser_vpp_stats('xe0',
                                                                    'TenGigabitEthernetff/6/0',
                                                                    output))

    def test_create_ipsec_tunnels(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out, \
                mock.patch.object(vpp_helpers.VatTerminal,
                                  'vat_terminal_exec_cmd_from_template') as \
                        mock_vat_terminal_exec_cmd_from_template, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'vpp_get_interface_data') as \
                        mock_ipsec_approx_setup_helper:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            mock_vat_terminal_exec_cmd_from_template.return_value = self.VPP_INTERFACES_DUMP
            mock_ipsec_approx_setup_helper.return_value = self.VPP_INTERFACES_DUMP
            sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
            self.assertIsNone(ipsec_approx_setup_helper.create_ipsec_tunnels())
        self.assertGreaterEqual(
            mock_vat_terminal_exec_cmd_from_template.call_count, 9)

    def test_create_ipsec_tunnels_cbc_algorithms(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS_CBC_ALGORITHMS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'find_encrypted_data_interface') as \
                        mock_find_encrypted_data_interface, \
                mock.patch.object(vpp_helpers.VatTerminal,
                                  'vat_terminal_exec_cmd_from_template') as \
                        mock_vat_terminal_exec_cmd_from_template, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'vpp_get_interface_data') as \
                        mock_ipsec_approx_setup_helper:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            mock_find_encrypted_data_interface.return_value = {
                'dpdk_port_num': 0,
                'driver': 'igb_uio',
                'dst_ip': '192.168.100.1',
                'dst_mac': '90:e2:ba:7c:30:e8',
                'ifname': 'xe0',
                'local_ip': '192.168.100.2',
                'local_mac': '90:e2:ba:7c:41:a8',
                'netmask': '255.255.255.0',
                'network': {},
                'node_name': 'vnf__1',
                'numa_node': 0,
                'peer_ifname': 'xe0',
                'peer_intf': {'dpdk_port_num': 0,
                              'driver': 'igb_uio',
                              'dst_ip': '192.168.100.2',
                              'dst_mac': '90:e2:ba:7c:41:a8',
                              'ifname': 'xe0',
                              'local_ip': '192.168.100.1',
                              'local_mac': '90:e2:ba:7c:30:e8',
                              'netmask': '255.255.255.0',
                              'network': {},
                              'node_name': 'tg__0',
                              'peer_ifname': 'xe0',
                              'peer_name': 'vnf__0',
                              'vld_id': 'uplink_0',
                              'vpci': '0000:81:00.0'},
                'peer_name': 'tg__0',
                'vld_id': 'uplink_0',
                'vpci': '0000:ff:06.0',
                'vpp_name': u'TenGigabitEthernetff/6/0',
                'vpp_sw_index': 1}
            mock_vat_terminal_exec_cmd_from_template.return_value = self.VPP_INTERFACES_DUMP
            mock_ipsec_approx_setup_helper.return_value = self.VPP_INTERFACES_DUMP
            sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
            self.assertIsNone(ipsec_approx_setup_helper.create_ipsec_tunnels())
        self.assertGreaterEqual(
            mock_vat_terminal_exec_cmd_from_template.call_count, 9)

    def test_find_raw_data_interface(self):
        expected = {'dpdk_port_num': 0,
                    'driver': 'igb_uio',
                    'dst_ip': '192.168.100.1',
                    'dst_mac': '90:e2:ba:7c:30:e8',
                    'ifname': 'xe0',
                    'local_ip': '192.168.100.2',
                    'local_mac': '90:e2:ba:7c:41:a8',
                    'netmask': '255.255.255.0',
                    'network': {},
                    'node_name': 'vnf__0',
                    'numa_node': 0,
                    'peer_ifname': 'xe0',
                    'peer_intf': {'dpdk_port_num': 0,
                                  'driver': 'igb_uio',
                                  'dst_ip': '192.168.100.2',
                                  'dst_mac': '90:e2:ba:7c:41:a8',
                                  'ifname': 'xe0',
                                  'local_ip': '192.168.100.1',
                                  'local_mac': '90:e2:ba:7c:30:e8',
                                  'netmask': '255.255.255.0',
                                  'network': {},
                                  'node_name': 'tg__0',
                                  'peer_ifname': 'xe0',
                                  'peer_name': 'vnf__0',
                                  'vld_id': 'uplink_0',
                                  'vpci': '0000:81:00.0'},
                    'peer_name': 'tg__0',
                    'vld_id': 'uplink_0',
                    'vpci': '0000:ff:06.0',
                    'vpp_name': u'TenGigabitEthernetff/6/0',
                    'vpp_sw_index': 1}
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(expected,
                         ipsec_approx_setup_helper.find_raw_data_interface())

    def test_find_raw_data_interface_error(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD_ERROR['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        with self.assertRaises(KeyError):
            ipsec_approx_setup_helper.find_raw_data_interface()

    def test_find_encrypted_data_interface(self):
        expected = {'dpdk_port_num': 1,
                    'driver': 'igb_uio',
                    'dst_ip': '1.1.1.2',
                    'dst_mac': '0a:b1:ec:fd:a2:66',
                    'ifname': 'xe1',
                    'local_ip': '1.1.1.1',
                    'local_mac': '4e:90:85:d3:c5:13',
                    'netmask': '255.255.255.0',
                    'network': {},
                    'node_name': 'vnf__0',
                    'numa_node': 0,
                    'peer_ifname': 'xe1',
                    'peer_intf': {'driver': 'igb_uio',
                                  'dst_ip': '1.1.1.1',
                                  'dst_mac': '4e:90:85:d3:c5:13',
                                  'ifname': 'xe1',
                                  'local_ip': '1.1.1.2',
                                  'local_mac': '0a:b1:ec:fd:a2:66',
                                  'netmask': '255.255.255.0',
                                  'network': {},
                                  'node_name': 'vnf__1',
                                  'peer_ifname': 'xe1',
                                  'peer_name': 'vnf__0',
                                  'vld_id': 'ciphertext',
                                  'vpci': '0000:00:07.0'},
                    'peer_name': 'vnf__1',
                    'vld_id': 'ciphertext',
                    'vpci': '0000:ff:07.0',
                    'vpp_name': u'VirtualFunctionEthernetff/7/0',
                    'vpp_sw_index': 2}
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)
        self.assertEqual(expected,
                         ipsec_approx_setup_helper.find_encrypted_data_interface())

    def test_create_startup_configuration_of_vpp(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsInstance(
            ipsec_approx_setup_helper.create_startup_configuration_of_vpp(),
            vpp_helpers.VppConfigGenerator)

    def test_add_worker_threads_and_rxqueues(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(
            ipsec_approx_setup_helper.add_worker_threads_and_rxqueues(
                vpp_config_generator, 1, 1))
        self.assertEqual(
            'cpu\n{\n  corelist-workers 2\n  main-core 1\n}\ndpdk\n{\n  ' \
            'dev default\n  {\n    num-rx-queues 1\n  }\n  num-mbufs 32768\n}\n',
            vpp_config_generator.dump_config())

    def test_add_worker_threads_and_rxqueues_smt(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_SMT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_SMT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(
            ipsec_approx_setup_helper.add_worker_threads_and_rxqueues(
                vpp_config_generator, 1))
        self.assertEqual(
            'cpu\n{\n  corelist-workers 2,6\n  main-core 1\n}\ndpdk\n{\n  ' \
            'dev default\n  {\n    num-rx-queues 1\n  }\n  num-mbufs 32768\n}\n',
            vpp_config_generator.dump_config())

    def test_add_worker_threads_and_rxqueues_with_numa(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(
            ipsec_approx_setup_helper.add_worker_threads_and_rxqueues(
                vpp_config_generator, 1, 1))
        self.assertEqual(
            'cpu\n{\n  corelist-workers 2\n  main-core 1\n}\ndpdk\n{\n  ' \
            'dev default\n  {\n    num-rx-queues 1\n  }\n  num-mbufs 32768\n}\n',
            vpp_config_generator.dump_config())

    def test_add_pci_devices(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(ipsec_approx_setup_helper.add_pci_devices(
            vpp_config_generator))
        self.assertEqual(
            'dpdk\n{\n  dev 0000:ff:06.0 \n  dev 0000:ff:07.0 \n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_cryptodev(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(ipsec_approx_setup_helper.add_dpdk_cryptodev(
            vpp_config_generator, 'aesni_gcm', 1))
        self.assertEqual(
            'dpdk\n{\n  vdev cryptodev_aesni_gcm_pmd,socket_id=0 \n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_cryptodev_hw(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS_HW
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(ipsec_approx_setup_helper.add_dpdk_cryptodev(
            vpp_config_generator, 'aesni_gcm', 1))
        self.assertEqual(
            'dpdk\n{\n  dev 0000:ff:01.0 \n  uio-driver igb_uio\n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_cryptodev_smt_used(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out:
            mock_get_cpu_layout.return_value = self.CPU_SMT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_LAYOUT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
        self.assertIsNone(ipsec_approx_setup_helper.add_dpdk_cryptodev(
            vpp_config_generator, 'aesni_gcm', 1))
        self.assertEqual(
            'dpdk\n{\n  vdev cryptodev_aesni_gcm_pmd,socket_id=0 \n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_cryptodev_smt_used_hw(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS_HW
        scenario_helper.all_options = self.ALL_OPTIONS
        vpp_config_generator = vpp_helpers.VppConfigGenerator()

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout:
            mock_get_cpu_layout.return_value = self.CPU_SMT
            ipsec_approx_setup_helper.sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper.sys_cores.cpuinfo = self.CPU_SMT
            ipsec_approx_setup_helper._update_vnfd_helper(
                ipsec_approx_setup_helper.sys_cores.get_cpu_layout())
            self.assertIsNone(ipsec_approx_setup_helper.add_dpdk_cryptodev(
                vpp_config_generator, 'aesni_gcm', 1))
        self.assertEqual(
            'dpdk\n{\n  dev 0000:ff:01.0 \n  dev 0000:ff:01.1 \n  uio-driver igb_uio\n}\n',
            vpp_config_generator.dump_config())

    def test_initialize_ipsec(self):
        vnfd_helper = VnfdHelper(
            TestVipsecApproxVnf.VNFD['vnfd:vnfd-catalog']['vnfd'][0])
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''
        scenario_helper = mock.Mock()
        scenario_helper.options = self.OPTIONS
        scenario_helper.all_options = self.ALL_OPTIONS

        ipsec_approx_setup_helper = VipsecApproxSetupEnvHelper(vnfd_helper,
                                                               ssh_helper,
                                                               scenario_helper)

        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'execute_script_json_out') as \
                        mock_execute_script_json_out, \
                mock.patch.object(vpp_helpers.VatTerminal,
                                  'vat_terminal_exec_cmd_from_template') as \
                        mock_vat_terminal_exec_cmd_from_template, \
                mock.patch.object(ipsec_approx_setup_helper,
                                  'vpp_get_interface_data') as \
                        mock_ipsec_approx_setup_helper:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            mock_execute_script_json_out.return_value = str(
                self.VPP_INTERFACES_DUMP).replace("\'", "\"")
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            mock_ipsec_approx_setup_helper.return_value = self.VPP_INTERFACES_DUMP
            sys_cores = cpu.CpuSysCores(ssh_helper)
            ipsec_approx_setup_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
            ipsec_approx_setup_helper.update_vpp_interface_data()
            ipsec_approx_setup_helper.iface_update_numa()
            self.assertIsNone(ipsec_approx_setup_helper.initialize_ipsec())
        self.assertGreaterEqual(
            mock_vat_terminal_exec_cmd_from_template.call_count, 9)
