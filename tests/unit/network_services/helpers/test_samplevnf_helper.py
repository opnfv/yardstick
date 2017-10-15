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
from __future__ import division

import unittest

import mock

from yardstick.network_services.helpers.samplevnf_helper import MultiPortConfig, PortPairs, \
    Core
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper

from tests.unit import STL_MOCKS


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper


class TestPortPairs(unittest.TestCase):
    def test_port_pairs_list(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = PortPairs(interfaces)
        self.assertEqual(port_pairs.port_pair_list, [("xe0", "xe1")])

    def test_valid_networks(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = PortPairs(interfaces)
        self.assertEqual(port_pairs.valid_networks, [("uplink_0", "downlink_0")])

    def test_all_ports(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = PortPairs(interfaces)
        self.assertEqual(set(port_pairs.all_ports), {"xe0", "xe1"})

    def test_uplink_ports(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = PortPairs(interfaces)
        self.assertEqual(port_pairs.uplink_ports, ["xe0"])

    def test_downlink_ports(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = PortPairs(interfaces)
        self.assertEqual(port_pairs.downlink_ports, ["xe1"])


class TestCoreTuple(unittest.TestCase):

    def test_init_no_socket(self):
        c = Core(core=8, hyperthread='h')
        self.assertEqual(c, Core(core=8, hyperthread=1))

    def test_init_no_core(self):
        with self.assertRaises(ValueError):
            Core(hyperthread=1)

    def test_init_no_thread(self):
        c = Core(socket=2, core=1)
        self.assertEqual(c, Core(core=1, socket=2))

    def test_eq(self):
        c1 = Core(core=1, hyperthread=2)
        c2 = Core(core=1, hyperthread=2)
        self.assertEqual(c1, c2)

    def test_iadd(self):
        c = Core(core=1)
        c += 2
        self.assertEqual(c, Core(core=3))

    def test___init__(self):
        core_tuple = Core(6)
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 0)
        self.assertEqual(str(core_tuple), "6")
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = Core('6')
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 0)
        self.assertEqual(str(core_tuple), "6")
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = Core('6h')
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 0)
        self.assertEqual(str(core_tuple), "6h")
        self.assertTrue(core_tuple.is_hyperthread())

        core_tuple = Core('s5c6')
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 5)
        self.assertEqual(str(core_tuple), "s5c6")
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = Core('s5c8h')
        self.assertEqual(core_tuple.core, 8)
        self.assertEqual(core_tuple.socket, 5)
        self.assertEqual(str(core_tuple), "s5c8h")
        self.assertTrue(core_tuple.is_hyperthread())

    def test__init___empty_string(self):
        with self.assertRaises(ValueError):
            Core("")

    def test___init__negative(self):
        bad_inputs = [
            '',
            '5s',
            '5s6',
            'c1s3',
            's',
            'h',
            'ch',
            '6hc1s0',
            '5 6h',
            [],
            {},
            object(),
        ]

        for bad_input in bad_inputs:
            with self.assertRaises(ValueError):
                try:
                    Core(bad_input)
                except ValueError:
                    raise
                else:
                    print("bad_input=[{}]".format(bad_input))


class TestMultiPortConfig(unittest.TestCase):

    VNFD_0 = {'short-name': 'VpeVnf',
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
                        [
                            {'virtual-interface':
                                {
                                    'dst_mac': '00:00:00:00:00:04',
                                    'vpci': '0000:05:00.0',
                                    'local_ip': '152.16.100.19',
                                    'type': 'PCI-PASSTHROUGH',
                                    'netmask': '255.255.255.0',
                                    'dpdk_port_num': 0,
                                    'bandwidth': '10 Gbps',
                                    'driver': "i40e",
                                    'dst_ip': '152.16.100.20',
                                    'ifname': 'xe0',
                                    'local_iface_name': 'eth0',
                                    'local_mac': '00:00:00:00:00:02',
                                    'vld_id': 'uplink_0',
                                },
                                'vnfd-connection-point-ref': 'xe0',
                                'name': 'xe0'},
                            {'virtual-interface':
                                {
                                    'dst_mac': '00:00:00:00:00:03',
                                    'vpci': '0000:05:00.1',
                                    'local_ip': '152.16.40.19',
                                    'type': 'PCI-PASSTHROUGH',
                                    'driver': "i40e",
                                    'netmask': '255.255.255.0',
                                    'dpdk_port_num': 1,
                                    'bandwidth': '10 Gbps',
                                    'dst_ip': '152.16.40.20',
                                    'ifname': 'xe1',
                                    'local_iface_name': 'eth1',
                                    'local_mac': '00:00:00:00:00:01',
                                    'vld_id': 'downlink_0',
                                },
                                'vnfd-connection-point-ref': 'xe1',
                                'name': 'xe1'}
                        ]}],
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
              'id': 'AclApproxVnf', 'name': 'VPEVnfSsh'}

    VNFD = {
        'vnfd:vnfd-catalog': {
            'vnfd': [
                VNFD_0,
            ]
        }
    }
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
                    'traffic_profile': 'ipv4_throughput_acl.yaml',
                    'traffic_options': {'flow': 'ipv4_Packets_acl.yaml',
                                        'imix': 'imix_voice.yaml'},
                    'type': 'ISB',
                    'nodes': {'tg__2': 'trafficgen_2.yardstick',
                              'tg__1': 'trafficgen_1.yardstick',
                              'vnf__1': 'vnf.yardstick'},
                    'topology': 'vpe-tg-topology-baremetal.yaml'}

    def setUp(self):
        super(TestMultiPortConfig, self).setUp()
        self.scenario_helper = ScenarioHelper("vnf")
        self.scenario_helper.scenario_cfg = self.scenario_cfg
        self.core_map = {'thread_per_core': '1', '2': ['1'], 'cores_per_socket': '2'}

    def test_validate_ip_and_prefixlen(self):
        ip_addr, prefix_len = MultiPortConfig.validate_ip_and_prefixlen('10.20.30.40', '16')
        self.assertEqual(ip_addr, '10.20.30.40')
        self.assertEqual(prefix_len, 16)

        ip_addr, prefix_len = MultiPortConfig.validate_ip_and_prefixlen('::1', '40')
        self.assertEqual(ip_addr, '0000:0000:0000:0000:0000:0000:0000:0001')
        self.assertEqual(prefix_len, 40)

    def test_validate_ip_and_prefixlen_negative(self):
        with self.assertRaises(AttributeError):
            MultiPortConfig.validate_ip_and_prefixlen('', '')

        with self.assertRaises(AttributeError):
            MultiPortConfig.validate_ip_and_prefixlen('10.20.30.400', '16')

        with self.assertRaises(AttributeError):
            MultiPortConfig.validate_ip_and_prefixlen('10.20.30.40', '33')

        with self.assertRaises(AttributeError):
            MultiPortConfig.validate_ip_and_prefixlen('::1', '129')

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test___init__(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        self.assertEqual(0, opnfv_vnf.swq)
        mock_os.path = mock.MagicMock()
        mock_os.path.isfile = mock.Mock(return_value=False)
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        self.assertEqual(0, opnfv_vnf.swq)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_update_timer(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        self.assertEqual(None, opnfv_vnf.update_timer())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_script(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'arp_route_tbl': '', 'arp_route_tbl6': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        self.assertIsNotNone(opnfv_vnf.generate_script(self.VNFD))
        opnfv_vnf.lb_config = 'HW'
        self.assertIsNotNone(opnfv_vnf.generate_script(self.VNFD))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_script_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.vnf_type = 'ACL'
        opnfv_vnf.generate_link_config = mock.Mock()
        opnfv_vnf.generate_arp_config = mock.Mock()
        opnfv_vnf.generate_arp_config6 = mock.Mock()
        opnfv_vnf.generate_action_config = mock.Mock()
        opnfv_vnf.generate_rule_config = mock.Mock()
        self.assertIsNotNone(opnfv_vnf.generate_script_data())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_rule_config(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'ACL'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.rules = ''
        self.assertIsNotNone(opnfv_vnf.generate_rule_config())
        opnfv_vnf.rules = 'new'
        self.assertIsNotNone(opnfv_vnf.generate_rule_config())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_action_config(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        self.assertIsNotNone(opnfv_vnf.generate_action_config())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_arp_config6(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        self.assertIsNotNone(opnfv_vnf.generate_arp_config6())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_arp_config(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        self.assertIsNotNone(opnfv_vnf.generate_arp_config())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_get_ports_gateway(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.assertIsNotNone(opnfv_vnf.get_ports_gateway('xe0'))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_get_ports_gateway6(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.assertIsNotNone(opnfv_vnf.get_ports_gateway6('xe0'))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_get_netmask_gateway(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.assertIsNotNone(opnfv_vnf.get_netmask_gateway('xe0'))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_get_netmask_gateway6(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        self.assertIsNotNone(opnfv_vnf.get_netmask_gateway6('xe0'))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_link_config(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()

        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.all_ports = ['32', '1', '987']
        opnfv_vnf.validate_ip_and_prefixlen = mock.Mock(return_value=('10.20.30.40', 16))

        result = opnfv_vnf.generate_link_config()
        self.assertEqual(len(result.splitlines()), 9)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_config(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.add_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.generate_lb_to_port_pair_mapping = mock.Mock()
        opnfv_vnf.generate_config_data = mock.Mock()
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.is_openstack = True
        self.assertIsNone(opnfv_vnf.generate_config())
        opnfv_vnf.is_openstack = False
        self.assertIsNone(opnfv_vnf.generate_config())

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    def test_get_config_tpl_data(self, *_):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = [['MASTER', [['mode', 'mode1'], ['type', 'filename']]]]
        self.assertIsNotNone(opnfv_vnf.get_config_tpl_data('filename'))

    @mock.patch('yardstick.network_services.helpers.iniparser.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    def test_get_txrx_tpl_data(self, *_):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = [
            [
                'MASTER',
                [
                    ['mode', 'mode1'],
                    ['pipeline_txrx_type', 'filename'],
                ],
            ],
        ]
        self.assertIsNotNone(opnfv_vnf.get_txrx_tpl_data('filename'))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_init_write_parser_template(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=True)
        opnfv_vnf.read_parser.get = mock.Mock(return_value='filename')

        self.assertIsNone(opnfv_vnf.find_pipeline_indexes())
        opnfv_vnf.write_parser.add_section = mock.MagicMock()
        opnfv_vnf.read_parser.item = mock.Mock(return_value=[1, 2, 3])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=False)
        opnfv_vnf.write_parser.set = mock.Mock()
        self.assertIsNone(opnfv_vnf.find_pipeline_indexes())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_init_write_parser_template_2(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        self.assertIsNone(opnfv_vnf.find_pipeline_indexes())

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_get_worker_threads(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        result = opnfv_vnf.get_worker_threads(1)
        self.assertEqual(1, result)
        opnfv_vnf.worker_config = '2t'
        result = opnfv_vnf.get_worker_threads(2)
        self.assertEqual(2, result)
        opnfv_vnf.worker_config = '2t'
        result = opnfv_vnf.get_worker_threads(3)
        self.assertEqual(2, result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_next_core_id(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        start_core = opnfv_vnf.generate_next_core_id(opnfv_vnf.start_core)
        self.assertEqual(start_core, Core(0, 1))

        opnfv_vnf.worker_config = '2t'
        opnfv_vnf.start_core = Core(0, 0, 0)
        start_core = opnfv_vnf.generate_next_core_id(opnfv_vnf.start_core)
        self.assertEqual(start_core, Core(0, 0, "h"))

        opnfv_vnf.worker_config = '2t'
        opnfv_vnf.start_core = Core(0, 0, "h")
        start_core = opnfv_vnf.generate_next_core_id(opnfv_vnf.start_core)
        self.assertEqual(start_core, Core(0, 1, 0))

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_lb_to_port_pair_mapping(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf._port_pairs = PortPairs(vnfd_mock.interfaces)
        opnfv_vnf.port_pair_list = opnfv_vnf._port_pairs.port_pair_list
        result = opnfv_vnf.generate_lb_to_port_pair_mapping()
        self.assertEqual(None, result)
        result = opnfv_vnf.set_priv_to_pub_mapping()
        self.assertEqual('(0,1)', result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_set_priv_que_handler(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        result = opnfv_vnf.set_priv_que_handler()
        self.assertEqual(None, result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_arp_route_tbl(self, *_):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        vnfd_mock.port_num.side_effect = ['32', '1', '987']
        vnfd_mock.find_interface.side_effect = [
            {
                'virtual-interface': {
                    'dst_ip': '10.20.30.40',
                    'netmask': '20',
                },
            },
            {
                'virtual-interface': {
                    'dst_ip': '10.200.30.40',
                    'netmask': '24',
                },
            },
            {
                'virtual-interface': {
                    'dst_ip': '10.20.3.40',
                    'netmask': '8',
                },
            },
        ]

        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.all_ports = [3, 2, 5]

        expected = 'routeadd net 32 10.20.30.40 0xfffff000\n' \
                   'routeadd net 1 10.200.30.40 0xffffff00\n' \
                   'routeadd net 987 10.20.3.40 0xff000000'
        result = opnfv_vnf.generate_arp_route_tbl()
        self.assertEqual(result, expected)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_arpicmp_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        result = opnfv_vnf.generate_arpicmp_data()
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'ovs'
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        result = opnfv_vnf.generate_arpicmp_data()
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'openstack'
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        result = opnfv_vnf.generate_arpicmp_data()
        self.assertIsNotNone(result)
        opnfv_vnf.lb_config = 'HW'
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        result = opnfv_vnf.generate_arpicmp_data()
        self.assertIsNotNone(result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_final_txrx_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.ports_len = 2
        opnfv_vnf.lb_index = 1
        opnfv_vnf.pktq_out_os = [1, 2]
        result = opnfv_vnf.generate_final_txrx_data(Core(0, 1))
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'openstack'
        opnfv_vnf.pktq_out_os = [1, 2]
        opnfv_vnf.lb_index = 1
        result = opnfv_vnf.generate_final_txrx_data(Core(0, 1))
        self.assertIsNotNone(result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_initial_txrx_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 2
        result = opnfv_vnf.generate_initial_txrx_data()
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'openstack'
        opnfv_vnf.pktq_out_os = [1, 2]
        result = opnfv_vnf.generate_initial_txrx_data()
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'ovs'
        opnfv_vnf.init_ovs = False
        opnfv_vnf.ovs_pktq_out = ''
        opnfv_vnf.pktq_out_os = [1, 2]
        opnfv_vnf.lb_index = 1
        result = opnfv_vnf.generate_initial_txrx_data()
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'ovs'
        opnfv_vnf.init_ovs = True
        opnfv_vnf.pktq_out_os = [1, 2]
        opnfv_vnf.ovs_pktq_out = ''
        opnfv_vnf.lb_index = 1
        result = opnfv_vnf.generate_initial_txrx_data()
        self.assertIsNotNone(result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_lb_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 2
        opnfv_vnf.prv_que_handler = 0
        result = opnfv_vnf.generate_lb_data()
        self.assertIsNotNone(result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_vnf_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 1
        opnfv_vnf.pktq_out = ['1', '2']
        opnfv_vnf.vnf_tpl = {'public_ip_port_range': '98164810',
                             'vnf_set': '(2,4,5)'}
        opnfv_vnf.prv_que_handler = 0
        result = opnfv_vnf.generate_vnf_data()
        self.assertIsNotNone(result)
        opnfv_vnf.lb_config = 'HW'
        opnfv_vnf.mul = 0.1
        result = opnfv_vnf.generate_vnf_data()
        self.assertIsNotNone(result)
        opnfv_vnf.lb_config = 'HW'
        opnfv_vnf.mul = 0.1
        opnfv_vnf.vnf_type = 'ACL'
        result = opnfv_vnf.generate_vnf_data()
        self.assertIsNotNone(result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_generate_config_data(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 1
        opnfv_vnf.pktq_out = ['1', '2']
        opnfv_vnf.prv_que_handler = 0
        opnfv_vnf.find_pipeline_indexes = mock.Mock()
        opnfv_vnf.arpicmp_tpl = mock.MagicMock()
        opnfv_vnf.txrx_tpl = mock.MagicMock()
        opnfv_vnf.loadb_tpl = mock.MagicMock()
        opnfv_vnf.vnf_tpl = {'public_ip_port_range': '98164810 (1,65535)',
                             'vnf_set': "(2,4,5)"}
        opnfv_vnf.generate_vnf_data = mock.Mock(return_value={})
        opnfv_vnf.add_pipeline = mock.Mock()
        result = opnfv_vnf.generate_config_data()
        self.assertIsNone(result)
        opnfv_vnf.generate_final_txrx_data = mock.Mock()
        opnfv_vnf.add_pipeline = mock.Mock()
        result = opnfv_vnf.generate_config_data()
        self.assertIsNone(result)
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 1
        opnfv_vnf.pktq_out = ['1', '2']
        opnfv_vnf.prv_que_handler = 0
        opnfv_vnf.find_pipeline_indexes = mock.Mock()
        opnfv_vnf.arpicmp_tpl = mock.MagicMock()
        opnfv_vnf.txrx_tpl = mock.MagicMock()
        opnfv_vnf.loadb_tpl = mock.MagicMock()
        opnfv_vnf.vnf_type = 'CGNAPT'
        opnfv_vnf.update_timer = mock.Mock()
        opnfv_vnf.port_pair_list = [("xe0", "xe1"), ("xe0", "xe2")]
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.generate_arpicmp_data = mock.Mock()
        result = opnfv_vnf.generate_config_data()
        self.assertIsNone(result)

    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.open')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.os')
    @mock.patch('yardstick.network_services.helpers.samplevnf_helper.YardstickConfigParser')
    def test_init_eal(self, mock_open, mock_os, ConfigParser):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = MultiPortConfig(self.scenario_helper, config_tpl, tmp_file, vnfd_mock, 'CGNAT',
                                    self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = mock.Mock(return_value=['MASTER'])
        opnfv_vnf.read_parser.has_option = mock.Mock(return_value=[])
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 1
        opnfv_vnf.pktq_out = ['1', '2']
        opnfv_vnf.prv_que_handler = 0
        opnfv_vnf.find_pipeline_indexes = mock.Mock()
        opnfv_vnf.arpicmp_tpl = mock.MagicMock()
        opnfv_vnf.txrx_tpl = mock.MagicMock()
        opnfv_vnf.loadb_tpl = mock.MagicMock()
        opnfv_vnf.vnf_tpl = {'public_ip_port_range': '98164810 (1,65535)'}
        opnfv_vnf.generate_vnf_data = mock.Mock(return_value={})
        opnfv_vnf.add_pipeline = mock.Mock()
        opnfv_vnf.tmp_file = "/tmp/config"
        result = opnfv_vnf.init_eal()
        self.assertIsNone(result)
