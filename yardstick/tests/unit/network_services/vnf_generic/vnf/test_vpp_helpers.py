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

from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from yardstick.network_services.vnf_generic.vnf.vpp_helpers import \
    VppSetupEnvHelper, VppConfigGenerator


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
