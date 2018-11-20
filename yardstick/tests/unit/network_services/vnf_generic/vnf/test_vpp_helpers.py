# Copyright (c) 2018 Viosoft Corporation
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
import ipaddress
import unittest

import mock

from yardstick.common import exceptions
from yardstick.network_services.helpers import cpu
from yardstick.network_services.vnf_generic.vnf import vpp_helpers
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services.vnf_generic.vnf.vpp_helpers import \
    VppSetupEnvHelper, VppConfigGenerator, VatTerminal


class TestVppConfigGenerator(unittest.TestCase):

    def test_add_config_item(self):
        test_item = {}
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_config_item(test_item, '/tmp/vpe.log',
                                             ['unix', 'log'])
        self.assertEqual({'unix': {'log': '/tmp/vpe.log'}}, test_item)

    def test_add_config_item_str(self):
        test_item = {'unix': ''}
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_config_item(test_item, '/tmp/vpe.log',
                                             ['unix', 'log'])
        self.assertEqual({'unix': {'log': '/tmp/vpe.log'}}, test_item)

    def test_add_unix_log(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_unix_log()
        self.assertEqual('unix\n{\n  log /tmp/vpe.log\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_unix_cli_listen(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_unix_cli_listen()
        self.assertEqual('unix\n{\n  cli-listen /run/vpp/cli.sock\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_unix_nodaemon(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_unix_nodaemon()
        self.assertEqual('unix\n{\n  nodaemon \n}\n',
                         vpp_config_generator.dump_config())

    def test_add_unix_coredump(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_unix_coredump()
        self.assertEqual('unix\n{\n  full-coredump \n}\n',
                         vpp_config_generator.dump_config())

    def test_add_dpdk_dev(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_dev('0000:00:00.0')
        self.assertEqual('dpdk\n{\n  dev 0000:00:00.0 \n}\n',
                         vpp_config_generator.dump_config())

    def test_add_dpdk_cryptodev(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_cryptodev(2, '0000:00:00.0')
        self.assertEqual(
            'dpdk\n{\n  dev 0000:00:01.0 \n  dev 0000:00:01.1 \n  uio-driver igb_uio\n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_sw_cryptodev(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_sw_cryptodev('aesni_gcm', 0, 2)
        self.assertEqual(
            'dpdk\n{\n  vdev cryptodev_aesni_gcm_pmd,socket_id=0 \n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_dev_default_rxq(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_dev_default_rxq(1)
        self.assertEqual(
            'dpdk\n{\n  dev default\n  {\n    num-rx-queues 1\n  }\n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_dev_default_rxd(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_dev_default_rxd(2048)
        self.assertEqual(
            'dpdk\n{\n  dev default\n  {\n    num-rx-desc 2048\n  }\n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_dev_default_txd(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_dev_default_txd(2048)
        self.assertEqual(
            'dpdk\n{\n  dev default\n  {\n    num-tx-desc 2048\n  }\n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_log_level(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_log_level('debug')
        self.assertEqual('dpdk\n{\n  log-level debug\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_dpdk_socketmem(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_socketmem('1024,1024')
        self.assertEqual('dpdk\n{\n  socket-mem 1024,1024\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_dpdk_num_mbufs(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_num_mbufs(32768)
        self.assertEqual('dpdk\n{\n  num-mbufs 32768\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_dpdk_uio_driver(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_uio_driver('igb_uio')
        self.assertEqual('dpdk\n{\n  uio-driver igb_uio\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_cpu_main_core(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_cpu_main_core('1,2')
        self.assertEqual('cpu\n{\n  main-core 1,2\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_cpu_corelist_workers(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_cpu_corelist_workers('1,2')
        self.assertEqual('cpu\n{\n  corelist-workers 1,2\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_heapsize(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_heapsize('4G')
        self.assertEqual('heapsize 4G\n', vpp_config_generator.dump_config())

    def test_add_ip6_hash_buckets(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_ip6_hash_buckets(2000000)
        self.assertEqual('ip6\n{\n  hash-buckets 2000000\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_ip6_heap_size(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_ip6_heap_size('4G')
        self.assertEqual('ip6\n{\n  heap-size 4G\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_ip_heap_size(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_ip_heap_size('4G')
        self.assertEqual('ip\n{\n  heap-size 4G\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_statseg_size(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_statseg_size('4G')
        self.assertEqual('statseg\n{\n  size 4G\n}\n',
                         vpp_config_generator.dump_config())

    def test_add_plugin(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_plugin('enable', ['dpdk_plugin.so'])
        self.assertEqual(
            'plugins\n{\n  plugin [\'dpdk_plugin.so\']\n  {\n    enable  \n  }\n}\n',
            vpp_config_generator.dump_config())

    def test_add_dpdk_no_multi_seg(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_no_multi_seg()
        self.assertEqual('dpdk\n{\n  no-multi-seg \n}\n',
                         vpp_config_generator.dump_config())

    def test_add_dpdk_no_tx_checksum_offload(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_dpdk_no_tx_checksum_offload()
        self.assertEqual('dpdk\n{\n  no-tx-checksum-offload \n}\n',
                         vpp_config_generator.dump_config())

    def test_dump_config(self):
        vpp_config_generator = VppConfigGenerator()
        vpp_config_generator.add_unix_log()
        self.assertEqual('unix\n{\n  log /tmp/vpe.log\n}\n',
                         vpp_config_generator.dump_config())

    def test_pci_dev_check(self):
        self.assertTrue(VppConfigGenerator.pci_dev_check('0000:00:00.0'))

    def test_pci_dev_check_error(self):
        with self.assertRaises(ValueError) as raised:
            VppConfigGenerator.pci_dev_check('0000:00:0.0')
        self.assertIn(
            'PCI address 0000:00:0.0 is not in valid format xxxx:xx:xx.x',
            str(raised.exception))


class TestVppSetupEnvHelper(unittest.TestCase):
    VNFD_0 = {
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

    VNFD_1 = {
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

    VNFD_2 = {
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

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ],
        },
    }

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

    VPP_INTERFACES_DUMP_MAC_ERR = [
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
            "l2_address": [144, 226, 186, 124, 65, 169, 0, 0],
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
            "l2_address": [78, 144, 133, 211, 197, 20, 0, 0],
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

    CPU_LAYOUT = {'cpuinfo': [[0, 0, 0, 0, 0, 0, 0, 0],
                              [1, 0, 0, 0, 0, 1, 1, 0]]}
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

    def test_kill_vnf(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, 0, 0
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper.kill_vnf()

    def test_kill_vnf_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 1, 0, 0
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        with self.assertRaises(RuntimeError) as raised:
            vpp_setup_env_helper.kill_vnf()

        self.assertIn('Failed to stop service vpp', str(raised.exception))

    def test_tear_down(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper.tear_down()

    def test_start_vpp_service(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, 0, 0
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper.start_vpp_service()

    def test_start_vpp_service_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 1, 0, 0
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        with self.assertRaises(RuntimeError) as raised:
            vpp_setup_env_helper.start_vpp_service()

        self.assertIn('Failed to start service vpp', str(raised.exception))

    def test__update_vnfd_helper(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper._update_vnfd_helper(
            {'vpp-data': {'vpp-key': 'vpp-value'}})

        self.assertEqual({'vpp-key': 'vpp-value'},
                         vpp_setup_env_helper.vnfd_helper.get('vpp-data', {}))

    def test__update_vnfd_helper_with_key(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper._update_vnfd_helper({'driver': 'qat'}, 'xe0')

        self.assertEqual('qat',
                         vpp_setup_env_helper.get_value_by_interface_key(
                             'xe0', 'driver'))

    def test__update_vnfd_helper_dict_without_key(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper._update_vnfd_helper(
            {'mgmt-interface': {'name': 'net'}})

        self.assertEqual({'ip': '10.10.10.101',
                          'name': 'net',
                          'password': 'r00t',
                          'user': 'root',
                          'vdu-id': 'ipsecvnf-baremetal'},
                         vpp_setup_env_helper.vnfd_helper.get('mgmt-interface',
                                                              {}))

    def test_get_value_by_interface_key(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper._update_vnfd_helper(
            {'vpp-data': {'vpp-key': 'vpp-value'}}, 'xe0')

        self.assertEqual({'vpp-key': 'vpp-value'},
                         vpp_setup_env_helper.get_value_by_interface_key(
                             'xe0', 'vpp-data'))

    def test_get_value_by_interface_key_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper._update_vnfd_helper(
            {'vpp-data': {'vpp-key': 'vpp-value'}}, 'xe0')

        self.assertIsNone(vpp_setup_env_helper.get_value_by_interface_key(
            'xe2', 'vpp-err'))

    def test_vpp_create_ipsec_tunnels(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        self.assertIsNone(
            vpp_setup_env_helper.vpp_create_ipsec_tunnels('10.10.10.2',
                                                          '10.10.10.1', 'xe0',
                                                          1, 1, mock.Mock(),
                                                          'crypto_key',
                                                          mock.Mock(),
                                                          'integ_key',
                                                          '20.20.20.0'))
        self.assertGreaterEqual(ssh_helper.execute.call_count, 2)

    def test_vpp_create_ipsec_1000_tunnels(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        self.assertIsNone(
            vpp_setup_env_helper.vpp_create_ipsec_tunnels('10.10.10.2',
                                                          '10.10.10.1', 'xe0',
                                                          1000, 128000,
                                                          mock.Mock(),
                                                          'crypto_key',
                                                          mock.Mock(),
                                                          'integ_key',
                                                          '20.20.20.0'))
        self.assertGreaterEqual(ssh_helper.execute.call_count, 2)

    def test_apply_config(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        self.assertIsNone(vpp_setup_env_helper.apply_config(mock.Mock()))
        self.assertGreaterEqual(ssh_helper.execute.call_count, 2)

    def test_apply_config_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 1, '', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        with self.assertRaises(RuntimeError) as raised:
            vpp_setup_env_helper.apply_config(mock.Mock())

        self.assertIn('Writing config file failed', str(raised.exception))

    def test_vpp_route_add(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertIsNone(
                vpp_setup_env_helper.vpp_route_add('xe0', '10.10.10.1', 24))

    def test_vpp_route_add_without_index(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertIsNone(
                vpp_setup_env_helper.vpp_route_add('xe0', '10.10.10.1', 24,
                                                   interface='xe0',
                                                   use_sw_index=False))

    def test_add_arp_on_dut(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertEqual('', vpp_setup_env_helper.add_arp_on_dut('xe0',
                                                                     '10.10.10.1',
                                                                     '00:00:00:00:00:00'))

    def test_set_ip(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertEqual('',
                             vpp_setup_env_helper.set_ip('xe0', '10.10.10.1',
                                                         24))

    def test_set_interface_state(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertEqual('',
                             vpp_setup_env_helper.set_interface_state('xe0',
                                                                      'up'))

    def test_set_interface_state_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
        with self.assertRaises(ValueError) as raised:
            vpp_setup_env_helper.set_interface_state('xe0', 'error')
        self.assertIn('Unexpected interface state: error',
                      str(raised.exception))

    def test_set_interface_down_state(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertEqual('',
                             vpp_setup_env_helper.set_interface_state('xe0',
                                                                      'down'))

    def test_vpp_set_interface_mtu(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = ''
            self.assertIsNone(
                vpp_setup_env_helper.vpp_set_interface_mtu('xe0', 9200))

    def test_vpp_interfaces_ready_wait(self):
        json_output = [self.VPP_INTERFACES_DUMP]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            self.assertIsNone(vpp_setup_env_helper.vpp_interfaces_ready_wait())

    def test_vpp_interfaces_ready_wait_timeout(self):
        json_output = [[
            {
                "sw_if_index": 0,
                "sup_sw_if_index": 0,
                "l2_address_length": 0,
                "l2_address": [0, 0, 0, 0, 0, 0, 0, 0],
                "interface_name": "xe0",
                "admin_up_down": 1,
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
            }]]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            with self.assertRaises(RuntimeError) as raised:
                vpp_setup_env_helper.vpp_interfaces_ready_wait(5)
            self.assertIn('timeout, not up [\'xe0\']', str(raised.exception))

    def test_vpp_get_interface_data(self):
        json_output = [self.VPP_INTERFACES_DUMP]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            self.assertEqual(json_output[0],
                             vpp_setup_env_helper.vpp_get_interface_data())

    def test_vpp_get_interface_data_ifname(self):
        json_output = [self.VPP_INTERFACES_DUMP]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            self.assertEqual(json_output[0][2],
                             vpp_setup_env_helper.vpp_get_interface_data(
                                 'VirtualFunctionEthernetff/7/0'))

    def test_vpp_get_interface_data_ifname_error(self):
        json_output = [self.VPP_INTERFACES_DUMP]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            self.assertEqual({}, vpp_setup_env_helper.vpp_get_interface_data(
                'error'))

    def test_vpp_get_interface_data_ifindex(self):
        json_output = [self.VPP_INTERFACES_DUMP]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            self.assertEqual(json_output[0][1],
                             vpp_setup_env_helper.vpp_get_interface_data(1))

    def test_vpp_get_interface_data_error(self):
        json_output = [self.VPP_INTERFACES_DUMP]
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)

        with mock.patch.object(vpp_helpers.VatTerminal,
                               'vat_terminal_exec_cmd_from_template') as \
                mock_vat_terminal_exec_cmd_from_template:
            mock_vat_terminal_exec_cmd_from_template.return_value = json_output
            with self.assertRaises(TypeError) as raised:
                vpp_setup_env_helper.vpp_get_interface_data(1.0)
        self.assertEqual('', str(raised.exception))

    def test_update_vpp_interface_data(self):
        output = '{}\n{}'.format(self.VPP_INTERFACES_DUMP,
                                 'dump_interface_table:6019: JSON output ' \
                                 'supported only for VPE API calls and dump_stats_table\n' \
                                 '/opt/nsb_bin/vpp/templates/dump_interfaces.vat(2): \n' \
                                 'dump_interface_table error: Misc')
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, output.replace("\'", "\""), ''
        ssh_helper.join_bin_path.return_value = '/opt/nsb_bin/vpp/templates'

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        self.assertIsNone(vpp_setup_env_helper.update_vpp_interface_data())
        self.assertGreaterEqual(ssh_helper.execute.call_count, 1)
        self.assertEqual('TenGigabitEthernetff/6/0',
                         vpp_setup_env_helper.get_value_by_interface_key(
                             'xe0', 'vpp_name'))
        self.assertEqual(1, vpp_setup_env_helper.get_value_by_interface_key(
            'xe0', 'vpp_sw_index'))
        self.assertEqual('VirtualFunctionEthernetff/7/0',
                         vpp_setup_env_helper.get_value_by_interface_key(
                             'xe1', 'vpp_name'))
        self.assertEqual(2, vpp_setup_env_helper.get_value_by_interface_key(
            'xe1', 'vpp_sw_index'))

    def test_update_vpp_interface_data_error(self):
        output = '{}\n{}'.format(self.VPP_INTERFACES_DUMP_MAC_ERR,
                                 'dump_interface_table:6019: JSON output ' \
                                 'supported only for VPE API calls and dump_stats_table\n' \
                                 '/opt/nsb_bin/vpp/templates/dump_interfaces.vat(2): \n' \
                                 'dump_interface_table error: Misc')
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, output.replace("\'", "\""), ''
        ssh_helper.join_bin_path.return_value = '/opt/nsb_bin/vpp/templates'

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        self.assertIsNone(vpp_setup_env_helper.update_vpp_interface_data())
        self.assertGreaterEqual(ssh_helper.execute.call_count, 1)

    def test_iface_update_numa(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '0', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        self.assertIsNone(vpp_setup_env_helper.iface_update_numa())
        self.assertGreaterEqual(ssh_helper.execute.call_count, 2)
        self.assertEqual(0, vpp_setup_env_helper.get_value_by_interface_key(
            'xe0', 'numa_node'))
        self.assertEqual(0, vpp_setup_env_helper.get_value_by_interface_key(
            'xe1', 'numa_node'))

    def test_iface_update_numa_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_1)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '-1', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout:
            mock_get_cpu_layout.return_value = self.CPU_LAYOUT
            sys_cores = cpu.CpuSysCores(ssh_helper)
            vpp_setup_env_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
        self.assertIsNone(vpp_setup_env_helper.iface_update_numa())
        self.assertGreaterEqual(ssh_helper.execute.call_count, 2)
        self.assertEqual(0, vpp_setup_env_helper.get_value_by_interface_key(
            'xe0', 'numa_node'))
        self.assertEqual(0, vpp_setup_env_helper.get_value_by_interface_key(
            'xe1', 'numa_node'))

    def test_iface_update_without_numa(self):
        vnfd_helper = VnfdHelper(self.VNFD_2)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, '-1', ''

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        with mock.patch.object(cpu.CpuSysCores, 'get_cpu_layout') as \
                mock_get_cpu_layout:
            mock_get_cpu_layout.return_value = self.CPU_SMT
            sys_cores = cpu.CpuSysCores(ssh_helper)
            vpp_setup_env_helper._update_vnfd_helper(
                sys_cores.get_cpu_layout())
        self.assertIsNone(vpp_setup_env_helper.iface_update_numa())
        self.assertGreaterEqual(ssh_helper.execute.call_count, 2)
        self.assertIsNone(vpp_setup_env_helper.get_value_by_interface_key(
            'xe0', 'numa_node'))
        self.assertIsNone(vpp_setup_env_helper.get_value_by_interface_key(
            'xe1', 'numa_node'))

    def test_execute_script(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        vpp_setup_env_helper.execute_script('dump_interfaces.vat', True, True)
        self.assertGreaterEqual(ssh_helper.put_file.call_count, 1)
        self.assertGreaterEqual(ssh_helper.execute.call_count, 1)

    def test_execute_script_error(self):
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.side_effect = Exception

        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        with self.assertRaises(Exception) as raised:
            vpp_setup_env_helper.execute_script('dump_interfaces.vat', True,
                                                True)
        self.assertIn(
            'VAT script execution failed: vpp_api_test json in dump_interfaces.vat script',
            str(raised.exception))
        self.assertGreaterEqual(ssh_helper.put_file.call_count, 1)

    def test_execute_script_json_out(self):
        json_output = [
            {
                "sw_if_index": 0,
                "sup_sw_if_index": 0
            },
            {
                "l2_address_length": 6,
                "l2_address": [144, 226, 186, 124, 65, 168, 0, 0]
            },
            {
                "interface_name": "VirtualFunctionEthernetff/7/0",
                "admin_up_down": 0
            }
        ]
        output = '{}\n{}'.format(json_output,
                                 'dump_interface_table:6019: JSON output ' \
                                 'supported only for VPE API calls and dump_stats_table\n' \
                                 '/opt/nsb_bin/vpp/templates/dump_interfaces.vat(2): \n' \
                                 'dump_interface_table error: Misc')
        vnfd_helper = VnfdHelper(self.VNFD_0)
        ssh_helper = mock.Mock()
        ssh_helper.execute.return_value = 0, output, ''
        ssh_helper.join_bin_path.return_value = '/opt/nsb_bin/vpp/templates'
        scenario_helper = mock.Mock()
        vpp_setup_env_helper = VppSetupEnvHelper(vnfd_helper, ssh_helper,
                                                 scenario_helper)
        self.assertEqual(str(json_output),
                         vpp_setup_env_helper.execute_script_json_out(
                             'dump_interfaces.vat'))

    def test_self_cleanup_vat_json_output(self):
        json_output = [
            {
                "sw_if_index": 0,
                "sup_sw_if_index": 0
            },
            {
                "l2_address_length": 6,
                "l2_address": [144, 226, 186, 124, 65, 168, 0, 0]
            },
            {
                "interface_name": "VirtualFunctionEthernetff/7/0",
                "admin_up_down": 0
            }
        ]

        output = '{}\n{}'.format(json_output,
                                 'dump_interface_table:6019: JSON output ' \
                                 'supported only for VPE API calls and dump_stats_table\n' \
                                 '/opt/nsb_bin/vpp/templates/dump_interfaces.vat(2): \n' \
                                 'dump_interface_table error: Misc')
        self.assertEqual(str(json_output),
                         VppSetupEnvHelper.cleanup_vat_json_output(output,
                                                                   '/opt/nsb_bin/vpp/templates/dump_interfaces.vat'))

    def test__convert_mac_to_number_list(self):
        self.assertEqual([144, 226, 186, 124, 65, 168],
                         VppSetupEnvHelper._convert_mac_to_number_list(
                             '90:e2:ba:7c:41:a8'))

    def test_get_vpp_interface_by_mac(self):
        mac_address = '90:e2:ba:7c:41:a8'
        self.assertEqual({'admin_up_down': 0,
                          'interface_name': 'TenGigabitEthernetff/6/0',
                          'l2_address': [144, 226, 186, 124, 65, 168, 0, 0],
                          'l2_address_length': 6,
                          'link_duplex': 2,
                          'link_speed': 32,
                          'link_up_down': 0,
                          'mtu': 9202,
                          'sub_default': 0,
                          'sub_dot1ad': 0,
                          'sub_exact_match': 0,
                          'sub_id': 0,
                          'sub_inner_vlan_id': 0,
                          'sub_inner_vlan_id_any': 0,
                          'sub_number_of_tags': 0,
                          'sub_outer_vlan_id': 0,
                          'sub_outer_vlan_id_any': 0,
                          'sup_sw_if_index': 1,
                          'sw_if_index': 1,
                          'vtr_op': 0,
                          'vtr_push_dot1q': 0,
                          'vtr_tag1': 0,
                          'vtr_tag2': 0},
                         VppSetupEnvHelper.get_vpp_interface_by_mac(
                             self.VPP_INTERFACES_DUMP, mac_address))

    def test_get_vpp_interface_by_mac_error(self):
        mac_address = '90:e2:ba:7c:41:a9'
        with self.assertRaises(ValueError) as raised:
            VppSetupEnvHelper.get_vpp_interface_by_mac(
                [{
                    "sw_if_index": 1,
                    "sup_sw_if_index": 1,
                    "l2_address_length": 7,
                    "l2_address": [144, 226, 186, 124, 65, 169, 0, 0],
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
                }], mac_address)

        self.assertIn('l2_address_length value is not 6.',
                      str(raised.exception))

    def test_get_vpp_interface_by_mac_l2_error(self):
        mac_address = '90:e2:ba:7c:41:a7'
        with self.assertRaises(KeyError) as raised:
            VppSetupEnvHelper.get_vpp_interface_by_mac(
                [{
                    "sw_if_index": 1,
                    "sup_sw_if_index": 1,
                    "l2_address_length": 6,
                    "l2_address_err": [144, 226, 186, 124, 65, 167, 0, 0],
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
                }], mac_address)

        self.assertIn(
            'key l2_address not found in interface dict.Probably input list ' \
            'is not parsed from correct VAT json output.',
            str(raised.exception))

    def test_get_vpp_interface_by_mac_l2_length_error(self):
        mac_address = '90:e2:ba:7c:41:a6'
        with self.assertRaises(KeyError) as raised:
            VppSetupEnvHelper.get_vpp_interface_by_mac(
                [{
                    "sw_if_index": 1,
                    "sup_sw_if_index": 1,
                    "l2_address_length_err": 6,
                    "l2_address": [144, 226, 186, 124, 65, 166, 0, 0],
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
                }], mac_address)

        self.assertIn(
            'key l2_address_length not found in interface dict. Probably ' \
            'input list is not parsed from correct VAT json output.',
            str(raised.exception))

    def test_get_prefix_length(self):
        start_ip = '10.10.10.0'
        end_ip = '10.10.10.127'
        ips = [ipaddress.ip_address(ip) for ip in
               [str(ipaddress.ip_address(start_ip)), str(end_ip)]]
        lowest_ip, highest_ip = min(ips), max(ips)

        self.assertEqual(25,
                         VppSetupEnvHelper.get_prefix_length(int(lowest_ip),
                                                             int(highest_ip),
                                                             lowest_ip.max_prefixlen))

    def test_get_prefix_length_zero_prefix(self):
        start_ip = '10.0.0.0'
        end_ip = '10.0.0.0'
        ips = [ipaddress.ip_address(ip) for ip in
               [str(ipaddress.ip_address(start_ip)), str(end_ip)]]
        lowest_ip, highest_ip = min(ips), max(ips)

        self.assertEqual(0,
                         VppSetupEnvHelper.get_prefix_length(int(lowest_ip),
                                                             int(highest_ip),
                                                             0))


class TestVatTerminal(unittest.TestCase):

    def test___init___error(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_open.side_effect = exceptions.SSHTimeout

        with self.assertRaises(RuntimeError) as raised:
            VatTerminal(ssh_helper, json_param=True)
        self.assertIn('Cannot open interactive terminal',
                      str(raised.exception))

    def test___init___exec_error(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.side_effect = exceptions.SSHTimeout
        VatTerminal(ssh_helper, json_param=True)

    def test_vat_terminal_exec_cmd(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.return_value = str(
            {'empty': 'value'}).replace("\'", "\"")
        vat_terminal = VatTerminal(ssh_helper, json_param=True)

        self.assertEqual({'empty': 'value'},
                         vat_terminal.vat_terminal_exec_cmd(
                             "hw_interface_set_mtu sw_if_index 1 mtu 9200"))

    def test_vat_terminal_exec_cmd_array(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.return_value = str(
            [{'empty': 'value'}]).replace("\'", "\"")
        vat_terminal = VatTerminal(ssh_helper, json_param=True)

        self.assertEqual([{'empty': 'value'}],
                         vat_terminal.vat_terminal_exec_cmd(
                             "hw_interface_set_mtu sw_if_index 1 mtu 9200"))

    def test_vat_terminal_exec_cmd_without_output(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.return_value = str(
            {'empty': 'value'}).replace("\'", "\"")
        vat_terminal = VatTerminal(ssh_helper, json_param=False)

        self.assertIsNone(vat_terminal.vat_terminal_exec_cmd(
            "hw_interface_set_mtu sw_if_index 1 mtu 9200"))

    def test_vat_terminal_exec_cmd_error(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.return_value = str(
            {'empty': 'value'}).replace("\'", "\"")
        ssh_helper.interactive_terminal_exec_command.side_effect = exceptions.SSHTimeout

        vat_terminal = VatTerminal(ssh_helper, json_param=True)

        with self.assertRaises(RuntimeError) as raised:
            vat_terminal.vat_terminal_exec_cmd(
                "hw_interface_set_mtu sw_if_index 1 mtu 9200")
        self.assertIn(
            'VPP not running on node. VAT command hw_interface_set_mtu ' \
            'sw_if_index 1 mtu 9200 execution failed',
            str(raised.exception))

    def test_vat_terminal_exec_cmd_output_error(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.return_value = str(
            'empty: value').replace("\'", "\"")

        vat_terminal = VatTerminal(ssh_helper, json_param=True)

        with self.assertRaises(RuntimeError) as raised:
            vat_terminal.vat_terminal_exec_cmd(
                "hw_interface_set_mtu sw_if_index 1 mtu 9200")
        self.assertIn(
            'VAT command hw_interface_set_mtu sw_if_index 1 mtu 9200: no JSON data.',
            str(raised.exception))

    def test_vat_terminal_close(self):
        ssh_helper = mock.Mock()
        vat_terminal = VatTerminal(ssh_helper, json_param=False)
        self.assertIsNone(vat_terminal.vat_terminal_close())

    def test_vat_terminal_close_error(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_exec_command.side_effect = exceptions.SSHTimeout
        vat_terminal = VatTerminal(ssh_helper, json_param=False)
        with self.assertRaises(RuntimeError) as raised:
            vat_terminal.vat_terminal_close()
        self.assertIn('Failed to close VAT console', str(raised.exception))

    def test_vat_terminal_close_vat_error(self):
        ssh_helper = mock.Mock()
        ssh_helper.interactive_terminal_close.side_effect = exceptions.SSHTimeout
        vat_terminal = VatTerminal(ssh_helper, json_param=False)
        with self.assertRaises(RuntimeError) as raised:
            vat_terminal.vat_terminal_close()
        self.assertIn('Cannot close interactive terminal',
                      str(raised.exception))

    def test_vat_terminal_exec_cmd_from_template(self):
        ssh_helper = mock.Mock()
        vat_terminal = VatTerminal(ssh_helper, json_param=False)

        with mock.patch.object(vat_terminal, 'vat_terminal_exec_cmd') as \
                mock_vat_terminal_exec_cmd:
            mock_vat_terminal_exec_cmd.return_value = 'empty'
            self.assertEqual(['empty'],
                             vat_terminal.vat_terminal_exec_cmd_from_template(
                                 "hw_interface_set_mtu.vat", sw_if_index=1,
                                 mtu=9200))
