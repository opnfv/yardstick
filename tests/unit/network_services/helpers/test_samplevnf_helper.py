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

import mock
import os
import six
import unittest

from copy import deepcopy

from yardstick.network_services.helpers import samplevnf_helper
from yardstick.network_services.vnf_generic.vnf.base import VnfdHelper
from tests.unit import STL_MOCKS


STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper
    from yardstick.network_services.helpers.iniparser import YardstickConfigParser


class TestPortPairs(unittest.TestCase):
    def test_port_pairs_list(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = samplevnf_helper.PortPairs(interfaces)
        self.assertEqual(port_pairs.port_pair_list, [("xe0", "xe1")])

    def test_valid_networks(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = samplevnf_helper.PortPairs(interfaces)
        self.assertEqual(port_pairs.valid_networks, [
                         ("uplink_0", "downlink_0")])

    def test_all_ports(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = samplevnf_helper.PortPairs(interfaces)
        self.assertEqual(set(port_pairs.all_ports), {"xe0", "xe1"})

    def test_uplink_ports(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = samplevnf_helper.PortPairs(interfaces)
        self.assertEqual(port_pairs.uplink_ports, ["xe0"])

    def test_downlink_ports(self):
        vnfd = TestMultiPortConfig.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        interfaces = vnfd['vdu'][0]['external-interface']
        port_pairs = samplevnf_helper.PortPairs(interfaces)
        self.assertEqual(port_pairs.downlink_ports, ["xe1"])


class TestCoreTuple(unittest.TestCase):

    def test_init_no_socket(self):
        c = samplevnf_helper.Core(core=8, hyperthread='h')
        self.assertEqual(c, samplevnf_helper.Core(core=8, hyperthread=1))

    def test_init_no_core(self):
        with self.assertRaises(ValueError):
            samplevnf_helper.Core(hyperthread=1)

    def test_init_no_thread(self):
        c = samplevnf_helper.Core(socket=2, core=1)
        self.assertEqual(c, samplevnf_helper.Core(core=1, socket=2))

    def test_eq(self):
        c1 = samplevnf_helper.Core(core=1, hyperthread=2)
        c2 = samplevnf_helper.Core(core=1, hyperthread=2)
        self.assertEqual(c1, c2)

    def test_iadd(self):
        c = samplevnf_helper.Core(core=1)
        c += 2
        self.assertEqual(c, samplevnf_helper.Core(core=3))

    def test___init__(self):
        core_tuple = samplevnf_helper.Core(6)
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 0)
        self.assertEqual(str(core_tuple), "6")
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = samplevnf_helper.Core('6')
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 0)
        self.assertEqual(str(core_tuple), "6")
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = samplevnf_helper.Core('6h')
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 0)
        self.assertEqual(str(core_tuple), "6h")
        self.assertTrue(core_tuple.is_hyperthread())

        core_tuple = samplevnf_helper.Core('s5c6')
        self.assertEqual(core_tuple.core, 6)
        self.assertEqual(core_tuple.socket, 5)
        self.assertEqual(str(core_tuple), "s5c6")
        self.assertFalse(core_tuple.is_hyperthread())

        core_tuple = samplevnf_helper.Core('s5c8h')
        self.assertEqual(core_tuple.core, 8)
        self.assertEqual(core_tuple.socket, 5)
        self.assertEqual(str(core_tuple), "s5c8h")
        self.assertTrue(core_tuple.is_hyperthread())

    def test__init___empty_string(self):
        with self.assertRaises(ValueError):
            samplevnf_helper.Core("")

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
                    samplevnf_helper.Core(bad_input)
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

    CGNAPT_CONFIG = [
        ['EAL', [['w', '0000:00:05.0'], ['w', '0000:00:03.0']]],
        ['PIPELINE0', [['type', 'MASTER'], ['core', '0']]],
        ['PIPELINE1',
         [['type', 'ARPICMP'],
          ['core', '1'],
          ['pktq_in', 'SWQ4'],
          ['pktq_out', 'TXQ0.0 TXQ1.0 TXQ2.0 TXQ3.0'],
          ['; egress (private interface) info', '@'],
          ['pktq_in_prv', 'RXQ0.0'],
          [';', '@'],
          [';for pub port <-> prv port mapping (prv, pub)', '@'],
          ['prv_to_pub_map', '(0,1)'],
          [';lib_arp_debug', '0']]],
        ['PIPELINE2',
         [['type', 'TIMER'],
          ['core', '0'],
          ['timer_dyn_timeout', '1000000'],
          ['n_flows', '1048576']]],
        ['PIPELINE3',
         [['type', 'TXRX'],
          ['core', '0'],
          ['pipeline_txrx_type', 'RXRX'],
          ['dest_if_offset', '176'],
          ['pktq_in', 'RXQ1.0 RXQ0.0'],
          ['pktq_out', 'SWQ2 SWQ3 SWQ0'],
          [';', '@']]],
        ['PIPELINE4',
         [['type', 'LOADB'],
          ['core', '1'],
          ['pktq_in', 'SWQ2 SWQ3'],
          ['pktq_out', 'SWQ4 SWQ5'],
          ['outport_offset', '136; 8'],
          ['n_vnf_threads', '1'],
          [';loadb_debug', '0']]],
        ['PIPELINE5',
         [['type', 'CGNAPT'],
          ['core', '2'],
          ['pktq_in', 'SWQ4 SWQ5'],
          ['pktq_out', 'SWQ6 SWQ7'],
          [';', '@'],
          ['; to make pipeline timer as 1-sec granularity', '@'],
          [';', '@'],
          ['phyport_offset', '204'],
          ['n_flows', '1048576'],
          ['key_offset', '192;64'],
          ['key_size', '8'],
          ['hash_offset', '200;72'],
          [';cgnapt_debug', '2'],
          [';', '@'],
          ['timer_period', '100'],
          ['max_clients_per_ip', '65535'],
          ['max_port_per_client', '100'],
          ['public_ip_port_range', '4040000:(1, 65535)'],
          ['vnf_set', '(3,4,5)'],
          ['pkt_type', 'ipv4'],
          ['cgnapt_meta_offset', '128'],
          ['prv_que_handler', '(0,)']]],
        ['PIPELINE6',
         [['type', 'TXRX'],
          ['core', '1'],
          ['pipeline_txrx_type', 'TXTX'],
          ['dest_if_offset', '176'],
          ['pktq_in', 'SWQ6 SWQ7 SWQ1'],
          ['pktq_out', 'TXQ1.0 TXQ0.0'],
          [';', '@']]]]

    def setUp(self):
        self._mock_open = mock.patch.object(six.moves.builtins, 'open')
        self.mock_open = self._mock_open.start()
        self._mock_os = mock.patch.object(os, 'path')
        self.mock_os = self._mock_os.start()
        self._mock_config_parser = mock.patch.object(
            samplevnf_helper, 'YardstickConfigParser')
        self.mock_config_parser = self._mock_config_parser.start()
        self.scenario_helper = ScenarioHelper("vnf")
        self.scenario_helper.scenario_cfg = self.scenario_cfg
        self.core_map = {'thread_per_core': '1', '2': ['1'], 'cores_per_socket': '2'}
        self.cgnapt_config = deepcopy(self.CGNAPT_CONFIG)

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_open.stop()
        self._mock_os.stop()
        self._mock_config_parser.stop()

    def test_validate_ip_and_prefixlen(self):
        ip_addr, prefix_len = (
            samplevnf_helper.MultiPortConfig.validate_ip_and_prefixlen(
                '10.20.30.40', '16'))
        self.assertEqual(ip_addr, '10.20.30.40')
        self.assertEqual(prefix_len, 16)

        ip_addr, prefix_len = (
            samplevnf_helper.MultiPortConfig.validate_ip_and_prefixlen(
                '::1', '40'))
        self.assertEqual(ip_addr, '0000:0000:0000:0000:0000:0000:0000:0001')
        self.assertEqual(prefix_len, 40)

    def test_validate_ip_and_prefixlen_negative(self):
        with self.assertRaises(AttributeError):
            samplevnf_helper.MultiPortConfig.validate_ip_and_prefixlen('', '')

        with self.assertRaises(AttributeError):
            samplevnf_helper.MultiPortConfig.validate_ip_and_prefixlen(
                '10.20.30.400', '16')

        with self.assertRaises(AttributeError):
            samplevnf_helper.MultiPortConfig.validate_ip_and_prefixlen(
                '10.20.30.40', '33')

        with self.assertRaises(AttributeError):
            samplevnf_helper.MultiPortConfig.validate_ip_and_prefixlen(
                '::1', '129')

    def test___init__(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        self.assertEqual(0, opnfv_vnf.swq)
        self.mock_os.path = mock.MagicMock()
        self.mock_os.path.isfile = mock.Mock(return_value=False)
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        self.assertEqual(0, opnfv_vnf.swq)

    def test_update_timer(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        self.assertEqual(None, opnfv_vnf.add_updated_timer())

    def test_generate_script(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'arp_route_tbl': '', 'arp_route_tbl6': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        self.assertIsNotNone(opnfv_vnf.generate_script(self.VNFD))
        opnfv_vnf.lb_config = 'HW'
        self.assertIsNotNone(opnfv_vnf.generate_script(self.VNFD))

    def test_generate_script_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.vnf_type = 'ACL'
        opnfv_vnf.generate_link_config = mock.Mock()
        opnfv_vnf.generate_arp_config = mock.Mock()
        opnfv_vnf.generate_arp_config6 = mock.Mock()
        opnfv_vnf.generate_action_config = mock.Mock()
        opnfv_vnf.generate_rule_config = mock.Mock()
        self.assertIsNotNone(opnfv_vnf.generate_script_data())

    def test_generate_rule_config(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'ACL'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.rules = ''
        self.assertIsNotNone(opnfv_vnf.generate_rule_config())
        opnfv_vnf.rules = 'new'
        self.assertIsNotNone(opnfv_vnf.generate_rule_config())

    def test_generate_action_config(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        self.assertIsNotNone(opnfv_vnf.generate_action_config())

    def test_generate_arp_config6(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        self.assertIsNotNone(opnfv_vnf.generate_arp_config6())

    def test_generate_arp_config(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.all_ports = ['xe0', 'xe1']
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
        opnfv_vnf.generate_script_data = \
            mock.Mock(return_value={'link_config': 0, 'arp_config': '',
                                    'arp_config6': '', 'actions': '',
                                    'rules': ''})
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.get_port_pairs = mock.Mock()
        opnfv_vnf.vnf_type = 'VFW'
        opnfv_vnf.get_ports_gateway = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.get_ports_gateway6 = mock.Mock(return_value=u'1.1.1.1')
        opnfv_vnf.get_netmask_gateway6 = mock.Mock(
            return_value=u'255.255.255.0')
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.interfaces = mock.MagicMock()
        opnfv_vnf.get_ports_gateway6 = mock.Mock()
        self.assertIsNotNone(opnfv_vnf.generate_arp_config())

    def test_get_ports_gateway(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
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

    def test_get_ports_gateway6(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
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

    def test_get_netmask_gateway(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
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

    def test_get_netmask_gateway6(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
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

    def test_generate_link_config(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()

        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
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
        opnfv_vnf.validate_ip_and_prefixlen = mock.Mock(
            return_value=('10.20.30.40', 16))

        result = opnfv_vnf.generate_link_config()
        self.assertEqual(len(result.splitlines()), 9)

    def test_generate_config(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.get_config_tpl_data = mock.MagicMock()
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.new_pipeline = mock.MagicMock()
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

    def test_get_config_tpl_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = [['MASTER', [['mode', 'mode1'], ['type', 'filename']]]]
        self.assertIsNotNone(opnfv_vnf.get_config_tpl_data('filename'))

    def test_get_txrx_tpl_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = [
            [
                'MASTER',
                [
                    ['mode', 'mode1'],
                    ['pipeline_txrx_type', 'filename'],
                ],
            ],
        ]
        self.assertIsNotNone(opnfv_vnf.get_txrx_tpl_data('filename'))

    def test_init_write_parser_template(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = YardstickConfigParser(semi='')
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.find_pipeline_indexes()
        self.assertEqual(opnfv_vnf.arpicmp_pipeline, 1)

    def test_init_write_parser_template_2(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = YardstickConfigParser(semi='')
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.find_pipeline_indexes()
        self.assertEqual(opnfv_vnf.arpicmp_pipeline, 1)

    def test_new_pipeline(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.pipeline_counter = 23
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = YardstickConfigParser(semi='')
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        txrx_tpl = opnfv_vnf.get_config_tpl_data('TXRX')
        s = opnfv_vnf.new_pipeline(txrx_tpl, {})
        self.assertEqual(s[0], 'PIPELINE23')
        self.assertEqual(opnfv_vnf.pipeline_counter, 24)

    def test_get_worker_threads(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
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

    # TODO(elfoley): Split this test into smaller tests
    def test_generate_next_core_id(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        start_core = opnfv_vnf.generate_next_core_id(opnfv_vnf.start_core)
        self.assertEqual(start_core, samplevnf_helper.Core(0, 1))

        opnfv_vnf.worker_config = '2t'
        opnfv_vnf.core_map = {'thread_per_core': '2', '2': ['1'], 'cores_per_socket': '2'}
        start_core = opnfv_vnf.generate_next_core_id(opnfv_vnf.start_core)
        self.assertEqual(start_core, samplevnf_helper.Core(0, 0, "h"))

    def test_generate_rxrx_core_id(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.core_map = {'thread_per_core': '1', '2': ['1'], 'cores_per_socket': '2'}
        rxrx_core, next_core = opnfv_vnf.generate_rxrx_core_id(opnfv_vnf.start_core, "share")
        self.assertEqual(rxrx_core, samplevnf_helper.Core(0, 0))
        self.assertEqual(next_core, samplevnf_helper.Core(0, 1))
        rxrx_core, next_core = opnfv_vnf.generate_rxrx_core_id(opnfv_vnf.start_core, "next")
        self.assertEqual(rxrx_core, samplevnf_helper.Core(0, 1))
        self.assertEqual(next_core, samplevnf_helper.Core(0, 2))

        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0, 0)
        opnfv_vnf.core_map = {'thread_per_core': '2', '2': ['1'], 'cores_per_socket': '2'}
        rxrx_core, next_core = opnfv_vnf.generate_rxrx_core_id(opnfv_vnf.start_core, "next")
        self.assertEqual(rxrx_core, samplevnf_helper.Core(0, 0, "h"))
        self.assertEqual(next_core, samplevnf_helper.Core(0, 1))
        rxrx_core, next_core = opnfv_vnf.generate_rxrx_core_id(opnfv_vnf.start_core, "share")
        self.assertEqual(rxrx_core, samplevnf_helper.Core(0, 0, "h"))
        self.assertEqual(next_core, samplevnf_helper.Core(0, 1))

        opnfv_vnf.worker_config = '2t'

    def test_generate_lb_to_port_pair_mapping(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf._port_pairs = samplevnf_helper.PortPairs(vnfd_mock.interfaces)
        opnfv_vnf.port_pair_list = opnfv_vnf._port_pairs.port_pair_list
        result = opnfv_vnf.generate_lb_to_port_pair_mapping()
        self.assertIsNone(result)
        result = opnfv_vnf.set_priv_to_pub_mapping()
        self.assertEqual('(0,1)', result)

    def test_set_priv_que_handler(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        result = opnfv_vnf.set_priv_que_handler()
        self.assertIsNone(result)

    def test_generate_arp_route_tbl(self):
        config_tpl = mock.Mock()
        tmp_file = ""
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

        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)

        opnfv_vnf.all_ports = [3, 2, 5]
        expected = 'routeadd net 32 10.20.30.40 0xfffff000\n' \
                   'routeadd net 1 10.200.30.40 0xffffff00\n' \
                   'routeadd net 987 10.20.3.40 0xff000000'
        result = opnfv_vnf.generate_arp_route_tbl()
        self.assertEqual(result, expected)

    def test_generate_arpicmp_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        result = opnfv_vnf.generate_arpicmp_data(opnfv_vnf.master_core)
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'ovs'
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        result = opnfv_vnf.generate_arpicmp_data(opnfv_vnf.master_core)
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'openstack'
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        result = opnfv_vnf.generate_arpicmp_data(opnfv_vnf.master_core)
        self.assertIsNotNone(result)
        opnfv_vnf.lb_config = 'HW'
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        result = opnfv_vnf.generate_arpicmp_data(opnfv_vnf.master_core)
        self.assertIsNotNone(result)

    def test_generate_final_txrx_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.ports_len = 2
        opnfv_vnf.lb_index = 1
        opnfv_vnf.pktq_out_os = [1, 2]
        result = opnfv_vnf.generate_final_txrx_data(samplevnf_helper.Core(0, 1))
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'openstack'
        opnfv_vnf.pktq_out_os = [1, 2]
        opnfv_vnf.lb_index = 1
        result = opnfv_vnf.generate_final_txrx_data(samplevnf_helper.Core(0, 1))
        self.assertIsNotNone(result)

    def test_generate_initial_txrx_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 2
        result = opnfv_vnf.generate_initial_txrx_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'openstack'
        opnfv_vnf.pktq_out_os = [1, 2]
        result = opnfv_vnf.generate_initial_txrx_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'ovs'
        opnfv_vnf.init_ovs = False
        opnfv_vnf.ovs_pktq_out = ''
        opnfv_vnf.pktq_out_os = [1, 2]
        opnfv_vnf.lb_index = 1
        result = opnfv_vnf.generate_initial_txrx_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)
        opnfv_vnf.nfv_type = 'ovs'
        opnfv_vnf.init_ovs = True
        opnfv_vnf.pktq_out_os = [1, 2]
        opnfv_vnf.ovs_pktq_out = ''
        opnfv_vnf.lb_index = 1
        result = opnfv_vnf.generate_initial_txrx_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)

    def test_generate_lb_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 2
        opnfv_vnf.prv_que_handler = 0
        result = opnfv_vnf.generate_lb_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)

    def test_generate_vnf_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.lb_count = 1
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.lb_index = 1
        opnfv_vnf.ports_len = 1
        opnfv_vnf.pktq_out = ['1', '2']
        opnfv_vnf.vnf_tpl = [
            'PIPELINE5',
            ['public_ip_port_range', '98164810'],
            ['vnf_set', '(2,4,5)'],
        ]
        opnfv_vnf.read_parser.section_get.return_value = '98164810'
        opnfv_vnf.prv_que_handler = 0
        result = opnfv_vnf.generate_vnf_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)
        opnfv_vnf.lb_config = 'HW'
        opnfv_vnf.mul = 0.1
        result = opnfv_vnf.generate_vnf_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)
        opnfv_vnf.lb_config = 'HW'
        opnfv_vnf.mul = 0.1
        opnfv_vnf.vnf_type = 'ACL'
        result = opnfv_vnf.generate_vnf_data(opnfv_vnf.start_core)
        self.assertIsNotNone(result)

    def test_generate_config_data(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = VnfdHelper(self.VNFD_0)
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.port_pair_list = [("xe0", "xe1")]
        opnfv_vnf.port_pairs = [("xe0", "xe1")]
        opnfv_vnf.txrx_pipeline = ''
        opnfv_vnf.rules = ''
        opnfv_vnf.write_parser = mock.MagicMock()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.read_parser.sections = self.cgnapt_config
        opnfv_vnf.write_parser.set = mock.Mock()
        opnfv_vnf.write_parser.add_section = mock.Mock()
        opnfv_vnf.read_parser.items = mock.MagicMock()
        opnfv_vnf.pipeline_counter = 0
        opnfv_vnf.worker_config = '1t'
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
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
        opnfv_vnf.new_pipeline = mock.Mock()
        result = opnfv_vnf.generate_config_data()
        self.assertIsNone(result)
        opnfv_vnf.generate_final_txrx_data = mock.Mock()
        opnfv_vnf.new_pipeline = mock.Mock()
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
        opnfv_vnf.add_updated_timer = mock.Mock()
        opnfv_vnf.port_pair_list = [("xe0", "xe1"), ("xe0", "xe2")]
        opnfv_vnf.lb_to_port_pair_mapping = [0, 1]
        opnfv_vnf.generate_arpicmp_data = mock.Mock()
        result = opnfv_vnf.generate_config_data()
        self.assertIsNone(result)

    def test_init_eal(self):
        config_tpl = mock.Mock()
        tmp_file = mock.Mock()
        vnfd_mock = mock.MagicMock()
        opnfv_vnf = samplevnf_helper.MultiPortConfig(self.scenario_helper, config_tpl, tmp_file,
                                                     vnfd_mock, 'CGNAT', self.core_map)
        opnfv_vnf.socket = 0
        opnfv_vnf.start_core = samplevnf_helper.Core(0, 0)
        opnfv_vnf.write_parser = YardstickConfigParser()
        opnfv_vnf.read_parser = mock.MagicMock()
        opnfv_vnf.vnfd = self.VNFD['vnfd:vnfd-catalog']['vnfd'][0]
        opnfv_vnf.interfaces = opnfv_vnf.vnfd['vdu'][0]['external-interface']
        opnfv_vnf.init_eal()
        self.assertEqual(opnfv_vnf.write_parser.sections[0], ['EAL', []])
