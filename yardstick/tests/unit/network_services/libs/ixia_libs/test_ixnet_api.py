# Copyright (c) 2018 Intel Corporation
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

import mock
import IxNetwork
import unittest

from copy import deepcopy

from yardstick.common import exceptions
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api


UPLINK = 'uplink'
DOWNLINK = 'downlink'

TRAFFIC_PARAMETERS = {
    UPLINK: {
        'id': 1,
        'bidir': 'False',
        'duration': 60,
        'rate': 10000.5,
        'rate_unit': 'fps',
        'outer_l2': {
            'framesize': {'64B': '25', '256B': '75'},
            'QinQ': None
        },
        'outer_l3': {
            'count': 512,
            'srcseed': 10,
            'dstseed': 20,
            'dscp': 0,
            'proto': 'udp',
            'ttl': 32,
            'dstip': '152.16.40.20',
            'srcip': '152.16.100.20',
            'dstmask': 24,
            'srcmask': 24
        },
        'outer_l4': {
            'seed': 1,
            'count': 1,
            'dstport': 2001,
            'srcport': 1234,
            'srcportmask': 0,
            'dstportmask': 0
        },
        'traffic_type': 'continuous'
    },
    DOWNLINK: {
        'id': 2,
        'bidir': 'False',
        'duration': 60,
        'rate': 75.2,
        'rate_unit': '%',
        'outer_l2': {
            'framesize': {'128B': '35', '1024B': '65'},
            'QinQ': None
        },
        'outer_l3': {
            'count': 1024,
            'srcseed': 30,
            'dstseed': 40,
            'dscp': 0,
            'proto': 'udp',
            'ttl': 32,
            'dstip': '2001::10',
            'srcip': '2021::10',
            'dstmask': 64,
            'srcmask': 64
        },
        'outer_l4': {
            'seed': 1,
            'count': 1,
            'dstport': 1234,
            'srcport': 2001,
            'srcportmask': 0,
            'dstportmask': 0
        },
        'traffic_type': 'continuous'
    }
}


class TestIxNextgen(unittest.TestCase):

    def setUp(self):
        self.ixnet = mock.Mock()
        self.ixnet.execute = mock.Mock()
        self.ixnet.getRoot.return_value = 'my_root'
        self.ixnet_gen = ixnet_api.IxNextgen()
        self.ixnet_gen._ixnet = self.ixnet

    def test_get_config(self):
        tg_cfg = {
            'vdu': [
                {
                    'external-interface': [
                        {'virtual-interface': {'vpci': '0000:07:00.1'}},
                        {'virtual-interface': {'vpci': '0001:08:01.2'}}
                    ]
                },
            ],
            'mgmt-interface': {
                'ip': 'test1',
                'tg-config': {
                    'dut_result_dir': 'test2',
                    'version': 'test3',
                    'ixchassis': 'test4',
                    'tcl_port': 'test5',
                },
            }
        }

        expected = {
            'machine': 'test1',
            'port': 'test5',
            'chassis': 'test4',
            'cards': ['0000', '0001'],
            'ports': ['07', '08'],
            'output_dir': 'test2',
            'version': 'test3',
            'bidir': True,
        }

        result = ixnet_api.IxNextgen.get_config(tg_cfg)
        self.assertEqual(result, expected)

    def test__get_config_element_by_flow_group_name(self):
        self.ixnet_gen._ixnet.getList.side_effect = [['traffic_item'],
                                                     ['fg_01']]
        self.ixnet_gen._ixnet.getAttribute.return_value = 'flow_group_01'
        output = self.ixnet_gen._get_config_element_by_flow_group_name(
            'flow_group_01')
        self.assertEqual('traffic_item/configElement:flow_group_01', output)

    def test__get_config_element_by_flow_group_name_no_match(self):
        self.ixnet_gen._ixnet.getList.side_effect = [['traffic_item'],
                                                     ['fg_01']]
        self.ixnet_gen._ixnet.getAttribute.return_value = 'flow_group_02'
        output = self.ixnet_gen._get_config_element_by_flow_group_name(
            'flow_group_01')
        self.assertIsNone(output)

    def test__get_stack_item(self):
        self.ixnet_gen._ixnet.getList.return_value = ['tcp1', 'tcp2', 'udp']
        with mock.patch.object(
                self.ixnet_gen, '_get_config_element_by_flow_group_name') as \
                mock_get_cfg_element:
            mock_get_cfg_element.return_value = 'cfg_element'
            output = self.ixnet_gen._get_stack_item(mock.ANY, ixnet_api.PROTO_TCP)
        self.assertEqual(['tcp1', 'tcp2'], output)

    def test__get_stack_item_no_config_element(self):
        with mock.patch.object(
                self.ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                self.ixnet_gen._get_stack_item(mock.ANY, mock.ANY)

    def test__get_field_in_stack_item(self):
        self.ixnet_gen._ixnet.getList.return_value = ['field1', 'field2']
        output = self.ixnet_gen._get_field_in_stack_item(mock.ANY, 'field2')
        self.assertEqual('field2', output)

    def test__get_field_in_stack_item_no_field_present(self):
        self.ixnet_gen._ixnet.getList.return_value = ['field1', 'field2']
        with self.assertRaises(exceptions.IxNetworkFieldNotPresentInStackItem):
            self.ixnet_gen._get_field_in_stack_item(mock.ANY, 'field3')

    def test__parse_framesize(self):
        framesize = {'64B': '75', '512b': '25'}
        output = self.ixnet_gen._parse_framesize(framesize)
        self.assertEqual(2, len(output))
        self.assertIn([64, 64, 75], output)
        self.assertIn([512, 512, 25], output)

    def test_add_topology(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.add_topology('topology 1', 'vports')
        self.ixnet_gen.ixnet.add.assert_called_once_with('my_root', 'topology')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'obj', '-name', 'topology 1', '-vports', 'vports')
        self.ixnet_gen.ixnet.commit.assert_called_once()

    def test_add_device_group(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.add_device_group('topology', 'device group 1', '1')
        self.ixnet_gen.ixnet.add.assert_called_once_with('topology',
                                                         'deviceGroup')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'obj', '-name', 'device group 1', '-multiplier', '1')
        self.ixnet_gen.ixnet.commit.assert_called_once()

    def test_add_ethernet(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.add_ethernet('device_group', 'ethernet 1')
        self.ixnet_gen.ixnet.add.assert_called_once_with('device_group',
                                                         'ethernet')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'obj', '-name', 'ethernet 1')
        self.ixnet_gen.ixnet.commit.assert_called_once()

    def test_add_vlans_single(self):
        obj = 'ethernet'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.ixnet_gen.ixnet.getList.return_value = ['vlan1', 'vlan2']
        vlan1 = ixnet_api.Vlan(vlan_id=100, tp_id='ethertype88a8', prio=2)
        vlan2 = ixnet_api.Vlan(vlan_id=101, tp_id='ethertype88a8', prio=3)
        self.ixnet_gen.add_vlans(obj, [vlan1, vlan2])
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('ethernet',
                                                               '-vlanCount', 2)
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('attr/singleValue',
                                                               '-value', 100)
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('attr/singleValue',
                                                               '-value', 101)
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('attr/singleValue',
                                                               '-value', 2)
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('attr/singleValue',
                                                               '-value', 3)
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', 'ethertype88a8')
        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test_add_vlans_increment(self):
        obj = 'ethernet'
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.ixnet_gen.ixnet.getList.return_value = ['vlan1']
        vlan = ixnet_api.Vlan(vlan_id=100, vlan_id_step=1, prio=3, prio_step=2)
        self.ixnet_gen.add_vlans(obj, [vlan])
        self.ixnet.setMultiAttribute.assert_any_call('obj', '-start', 100,
                                                     '-step', 1,
                                                     '-direction', 'increment')
        self.ixnet.setMultiAttribute.assert_any_call('obj', '-start', 3,
                                                     '-step', 2,
                                                     '-direction', 'increment')

        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test_add_vlans_invalid(self):
        vlans = []
        self.assertRaises(RuntimeError, self.ixnet_gen.add_vlans, 'obj', vlans)

    def test_add_ipv4(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.add_ipv4('ethernet 1', name='ipv4 1')
        self.ixnet_gen.ixnet.add.assert_called_once_with('ethernet 1', 'ipv4')
        self.ixnet_gen.ixnet.setAttribute.assert_called_once_with('obj',
                                                                  '-name',
                                                                  'ipv4 1')
        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test_add_ipv4_single(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.ixnet_gen.add_ipv4('ethernet 1', name='ipv4 1', addr='100.1.1.100',
                                prefix='24', gateway='100.1.1.200')
        self.ixnet_gen.ixnet.add.assert_called_once_with('ethernet 1', 'ipv4')
        self.ixnet_gen.ixnet.setAttribute.assert_called_once_with('obj',
                                                                  '-name',
                                                                  'ipv4 1')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', '100.1.1.100')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', '24')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', '100.1.1.200')

        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test_add_ipv4_counter(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.ixnet_gen.add_ipv4('ethernet 1', name='ipv4 1',
                                addr='100.1.1.100',
                                addr_step='1',
                                addr_direction='increment',
                                prefix='24',
                                gateway='100.1.1.200',
                                gw_step='1',
                                gw_direction='increment')
        self.ixnet_gen.ixnet.add.assert_any_call('ethernet 1', 'ipv4')
        self.ixnet_gen.ixnet.setAttribute.assert_called_once_with('obj',
                                                                  '-name',
                                                                  'ipv4 1')
        self.ixnet_gen.ixnet.add.assert_any_call('attr', 'counter')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('obj', '-start',
                                                               '100.1.1.100',
                                                               '-step', '1',
                                                               '-direction',
                                                               'increment')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', '24')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call('obj', '-start',
                                                               '100.1.1.200',
                                                               '-step', '1',
                                                               '-direction',
                                                               'increment')
        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test_add_pppox_client(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.ixnet_gen.add_pppox_client('ethernet 1', 'pap', 'user', 'pwd')
        self.ixnet_gen.ixnet.add.assert_called_once_with('ethernet 1',
                                                         'pppoxclient')

        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', 'pap')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', 'user')
        self.ixnet_gen.ixnet.setMultiAttribute.assert_any_call(
            'attr/singleValue', '-value', 'pwd')

        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test_add_pppox_client_invalid_auth(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.assertRaises(NotImplementedError, self.ixnet_gen.add_pppox_client,
                          'ethernet 1', 'invalid_auth', 'user', 'pwd')

        self.ixnet_gen.ixnet.setMultiAttribute.assert_not_called()

    def test_add_bgp(self):
        self.ixnet_gen.ixnet.add.return_value = 'obj'
        self.ixnet_gen.ixnet.getAttribute.return_value = 'attr'
        self.ixnet_gen.add_bgp(ipv4='ipv4 1',
                               dut_ip='10.0.0.1',
                               local_as=65000,
                               bgp_type='external')
        self.ixnet_gen.ixnet.add.assert_called_once_with('ipv4 1', 'bgpIpv4Peer')
        self.ixnet_gen.ixnet.setAttribute.assert_any_call(
            'attr/singleValue', '-value', '10.0.0.1')
        self.ixnet_gen.ixnet.setAttribute.assert_any_call(
            'attr/singleValue', '-value', 65000)
        self.ixnet_gen.ixnet.setAttribute.assert_any_call(
            'attr/singleValue', '-value', 'external')

    @mock.patch.object(IxNetwork, 'IxNet')
    def test_connect(self, mock_ixnet):
        mock_ixnet.return_value = self.ixnet
        with mock.patch.object(self.ixnet_gen, 'get_config') as mock_config:
            mock_config.return_value = {'machine': 'machine_fake',
                                        'port': 'port_fake',
                                        'version': 12345}
            self.ixnet_gen.connect(mock.ANY)

        self.ixnet.connect.assert_called_once_with(
            'machine_fake', '-port', 'port_fake', '-version', '12345')
        mock_config.assert_called_once()

    def test_connect_invalid_config_no_machine(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={
            'port': 'port_fake',
            'version': '12345'})
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_invalid_config_no_port(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={
            'machine': 'machine_fake',
            'version': '12345'})
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_invalid_config_no_version(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={
            'machine': 'machine_fake',
            'port': 'port_fake'})
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_no_config(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={})
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_clear_config(self):
        self.ixnet_gen.clear_config()
        self.ixnet.execute.assert_called_once_with('newConfig')

    @mock.patch.object(ixnet_api, 'log')
    def test_assign_ports_2_ports(self, *args):
        self.ixnet.getAttribute.side_effect = ['up', 'down']
        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['2', '2']}
        self.ixnet_gen._cfg = config

        self.assertIsNone(self.ixnet_gen.assign_ports())
        self.assertEqual(self.ixnet.execute.call_count, 1)
        self.assertEqual(self.ixnet.commit.call_count, 3)
        self.assertEqual(self.ixnet.getAttribute.call_count, 2)

    @mock.patch.object(ixnet_api, 'log')
    def test_assign_ports_port_down(self, mock_log):
        self.ixnet.getAttribute.return_value = 'down'
        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['3', '4']}
        self.ixnet_gen._cfg = config
        self.ixnet_gen.assign_ports()
        mock_log.warning.assert_called()

    def test_assign_ports_no_config(self):
        self.ixnet_gen._cfg = {}
        self.assertRaises(KeyError, self.ixnet_gen.assign_ports)

    def test__create_traffic_item(self):
        self.ixnet.add.return_value = 'my_new_traffic_item'
        self.ixnet.remapIds.return_value = ['my_traffic_item_id']

        self.ixnet_gen._create_traffic_item()
        self.ixnet.add.assert_called_once_with(
            'my_root/traffic', 'trafficItem')
        self.ixnet.setMultiAttribute.assert_called_once_with(
            'my_new_traffic_item', '-name', 'RFC2544', '-trafficType', 'raw')
        self.assertEqual(2, self.ixnet.commit.call_count)
        self.ixnet.remapIds.assert_called_once_with('my_new_traffic_item')
        self.ixnet.setAttribute('my_traffic_item_id/tracking',
                                '-trackBy', 'trafficGroupId0')

    def test__create_flow_groups(self):
        uplink_endpoints = ['up_endp1', 'up_endp2']
        downlink_endpoints = ['down_endp1', 'down_endp2']
        self.ixnet_gen.ixnet.getList.side_effect = [['traffic_item'], ['1', '2']]
        self.ixnet_gen.ixnet.add.side_effect = ['endp1', 'endp2', 'endp3',
                                                'endp4']
        self.ixnet_gen._create_flow_groups(uplink_endpoints, downlink_endpoints)
        self.ixnet_gen.ixnet.add.assert_has_calls([
            mock.call('traffic_item', 'endpointSet'),
            mock.call('traffic_item', 'endpointSet')])
        self.ixnet_gen.ixnet.setMultiAttribute.assert_has_calls([
            mock.call('endp1', '-name', '1', '-sources', ['up_endp1'],
                      '-destinations', ['down_endp1']),
            mock.call('endp2', '-name', '2', '-sources', ['down_endp1'],
                      '-destinations', ['up_endp1']),
            mock.call('endp3', '-name', '3', '-sources', ['up_endp2'],
                      '-destinations', ['down_endp2']),
            mock.call('endp4', '-name', '4', '-sources', ['down_endp2'],
                      '-destinations', ['up_endp2'])])

    def test__append_protocol_to_stack(self):

        self.ixnet_gen._append_procotol_to_stack('my_protocol', 'prev_element')
        self.ixnet.execute.assert_called_with(
            'append', 'prev_element',
            'my_root/traffic/protocolTemplate:"my_protocol"')

    def test__setup_config_elements(self):
        self.ixnet_gen.ixnet.getList.side_effect = [['traffic_item'],
                                               ['cfg_element']]
        with mock.patch.object(self.ixnet_gen, '_append_procotol_to_stack') as \
                mock_append_proto:
            self.ixnet_gen._setup_config_elements()
        mock_append_proto.assert_has_calls([
            mock.call(ixnet_api.PROTO_UDP, 'cfg_element/stack:"ethernet-1"'),
            mock.call(ixnet_api.PROTO_IPV4, 'cfg_element/stack:"ethernet-1"')])
        self.ixnet_gen.ixnet.setAttribute.assert_has_calls([
            mock.call('cfg_element/frameRateDistribution', '-portDistribution',
                      'splitRateEvenly'),
            mock.call('cfg_element/frameRateDistribution',
                      '-streamDistribution', 'splitRateEvenly')])

    @mock.patch.object(ixnet_api.IxNextgen, '_create_traffic_item')
    @mock.patch.object(ixnet_api.IxNextgen, '_create_flow_groups')
    @mock.patch.object(ixnet_api.IxNextgen, '_setup_config_elements')
    def test_create_traffic_model(self, mock__setup_config_elements,
                                  mock__create_flow_groups,
                                  mock__create_traffic_item):
        uplink_ports = ['port1', 'port3']
        downlink_ports = ['port2', 'port4']
        uplink_endpoints = ['port1/protocols', 'port3/protocols']
        downlink_endpoints = ['port2/protocols', 'port4/protocols']
        self.ixnet_gen.create_traffic_model(uplink_ports, downlink_ports)
        mock__create_traffic_item.assert_called_once_with('raw')
        mock__create_flow_groups.assert_called_once_with(uplink_endpoints,
                                                         downlink_endpoints)
        mock__setup_config_elements.assert_called_once()

    @mock.patch.object(ixnet_api.IxNextgen, '_create_traffic_item')
    @mock.patch.object(ixnet_api.IxNextgen, '_create_flow_groups')
    @mock.patch.object(ixnet_api.IxNextgen, '_setup_config_elements')
    def test_create_ipv4_traffic_model(self, mock__setup_config_elements,
                                       mock__create_flow_groups,
                                       mock__create_traffic_item):
        uplink_topologies = ['up1', 'up3']
        downlink_topologies = ['down2', 'down4']
        self.ixnet_gen.create_ipv4_traffic_model(uplink_topologies,
                                                 downlink_topologies)
        mock__create_traffic_item.assert_called_once_with('ipv4')
        mock__create_flow_groups.assert_called_once_with(uplink_topologies,
                                                         downlink_topologies)
        mock__setup_config_elements.assert_called_once_with(False)

    def test__update_frame_mac(self):
        with mock.patch.object(self.ixnet_gen, '_get_field_in_stack_item') as \
                mock_get_field:
            mock_get_field.return_value = 'field_descriptor'
            self.ixnet_gen._update_frame_mac('ethernet_descriptor', 'field', 'mac')
        mock_get_field.assert_called_once_with('ethernet_descriptor', 'field')
        self.ixnet_gen.ixnet.setMultiAttribute(
            'field_descriptor', '-singleValue', 'mac', '-fieldValue', 'mac',
            '-valueType', 'singleValue')
        self.ixnet_gen.ixnet.commit.assert_called_once()

    def test_update_frame(self):
        with mock.patch.object(
                self.ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value='cfg_element'), \
                mock.patch.object(self.ixnet_gen, '_update_frame_mac') as \
                mock_update_frame, \
                mock.patch.object(self.ixnet_gen, '_get_stack_item') as \
                mock_get_stack_item:
            mock_get_stack_item.side_effect = [['item1'], ['item2'],
                                               ['item3'], ['item4']]
            self.ixnet_gen.update_frame(TRAFFIC_PARAMETERS, 50)

        self.assertEqual(6, len(self.ixnet_gen.ixnet.setMultiAttribute.mock_calls))
        self.assertEqual(4, len(mock_update_frame.mock_calls))

        self.ixnet_gen.ixnet.setMultiAttribute.assert_has_calls([
            mock.call('cfg_element/transmissionControl',
                      '-type', 'continuous', '-duration', 50)
        ])

    def test_update_frame_qinq(self):
        with mock.patch.object(self.ixnet_gen,
                               '_get_config_element_by_flow_group_name',
                               return_value='cfg_element'), \
             mock.patch.object(self.ixnet_gen, '_update_frame_mac'),\
             mock.patch.object(self.ixnet_gen, '_get_stack_item',
                               return_value='item'), \
             mock.patch.object(self.ixnet_gen, '_get_field_in_stack_item',
                               return_value='field'):

            traffic_parameters = deepcopy(TRAFFIC_PARAMETERS)
            traffic_parameters[UPLINK]['outer_l2']['QinQ'] = {
                'S-VLAN': {'id': 128,
                           'priority': 1,
                           'cfi': 0},
                'C-VLAN': {'id': 512,
                           'priority': 0,
                           'cfi': 2}
            }

            self.ixnet_gen.update_frame(traffic_parameters, 50)

        self.ixnet_gen.ixnet.setMultiAttribute.assert_has_calls([
            mock.call('field', '-auto', 'false', '-singleValue', '0x88a8',
                      '-fieldValue', '0x88a8', '-valueType', 'singleValue'),
            mock.call('field', '-auto', 'false', '-singleValue', 1,
                      '-fieldValue', 1, '-valueType', 'singleValue'),
            mock.call('field', '-auto', 'false', '-singleValue', 128,
                      '-fieldValue', 128, '-valueType', 'singleValue'),
            mock.call('field', '-auto', 'false', '-singleValue', 512,
                      '-fieldValue', 512, '-valueType', 'singleValue'),
            mock.call('field', '-auto', 'false', '-singleValue', 2,
                      '-fieldValue', 2, '-valueType', 'singleValue')
        ], any_order=True)

    def test_update_frame_flow_not_present(self):
        with mock.patch.object(
                self.ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                self.ixnet_gen.update_frame(TRAFFIC_PARAMETERS, 40)

    def test_get_statistics(self):
        port_statistics = '::ixNet::OBJ-/statistics/view:"Port Statistics"'
        flow_statistics = '::ixNet::OBJ-/statistics/view:"Flow Statistics"'
        with mock.patch.object(self.ixnet_gen, '_build_stats_map') as \
                mock_build_stats:
            self.ixnet_gen.get_statistics()

        mock_build_stats.assert_has_calls([
            mock.call(port_statistics, self.ixnet_gen.PORT_STATS_NAME_MAP),
            mock.call(flow_statistics, self.ixnet_gen.LATENCY_NAME_MAP)])

    def test__set_flow_tracking(self):
        self.ixnet_gen._ixnet.getList.return_value = ['traffic_item']
        self.ixnet_gen._set_flow_tracking(track_by=['vlanVlanId0'])
        self.ixnet_gen.ixnet.setAttribute.assert_called_once_with(
            'traffic_item/tracking', '-trackBy', ['vlanVlanId0'])
        self.assertEqual(self.ixnet.commit.call_count, 1)

    def test__set_egress_flow_tracking(self):
        self.ixnet_gen._ixnet.getList.side_effect = [['traffic_item'],
                                                     ['encapsulation']]
        self.ixnet_gen._set_egress_flow_tracking(encapsulation='Ethernet',
                                                 offset='IPv4 TOS Precedence')
        self.ixnet_gen.ixnet.setAttribute.assert_any_call(
            'traffic_item', '-egressEnabled', True)
        self.ixnet_gen.ixnet.setAttribute.assert_any_call(
            'encapsulation', '-encapsulation', 'Ethernet')
        self.ixnet_gen.ixnet.setAttribute.assert_any_call(
            'encapsulation', '-offset', 'IPv4 TOS Precedence')
        self.assertEqual(self.ixnet.commit.call_count, 2)

    def test__update_ipv4_address(self):
        with mock.patch.object(self.ixnet_gen, '_get_field_in_stack_item',
                               return_value='field_desc'):
            self.ixnet_gen._update_ipv4_address(mock.ANY, mock.ANY, '192.168.1.1',
                                           100, 26, 25)
        self.ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'field_desc', '-seed', 100, '-fixedBits', '192.168.1.1',
            '-randomMask', '0.0.0.63', '-valueType', 'random',
            '-countValue', 25)

    def test__update_udp_port(self):
        with mock.patch.object(self.ixnet_gen, '_get_field_in_stack_item',
                               return_value='field_desc'):
            self.ixnet_gen._update_udp_port(mock.ANY, mock.ANY, 1234,
                                            2, 0, 2)

        self.ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'field_desc',
            '-auto', 'false',
            '-seed', 1,
            '-fixedBits', 1234,
            '-randomMask', 0,
            '-valueType', 'random',
            '-countValue', 1)

    def test_update_ip_packet(self):
        with mock.patch.object(self.ixnet_gen, '_update_ipv4_address') as \
                mock_update_add, \
                mock.patch.object(self.ixnet_gen, '_get_stack_item'), \
                mock.patch.object(self.ixnet_gen,
                '_get_config_element_by_flow_group_name', return_value='celm'):
            self.ixnet_gen.update_ip_packet(TRAFFIC_PARAMETERS)

        self.assertEqual(4, len(mock_update_add.mock_calls))

    def test_update_ip_packet_exception_no_config_element(self):
        with mock.patch.object(self.ixnet_gen,
                               '_get_config_element_by_flow_group_name',
                               return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                self.ixnet_gen.update_ip_packet(TRAFFIC_PARAMETERS)

    def test_update_l4(self):
        with mock.patch.object(self.ixnet_gen, '_update_udp_port') as \
                mock_update_udp, \
                mock.patch.object(self.ixnet_gen, '_get_stack_item'), \
                mock.patch.object(self.ixnet_gen,
                '_get_config_element_by_flow_group_name', return_value='celm'):
            self.ixnet_gen.update_l4(TRAFFIC_PARAMETERS)

        self.assertEqual(4, len(mock_update_udp.mock_calls))

    def test_update_l4_exception_no_config_element(self):
        with mock.patch.object(self.ixnet_gen,
                               '_get_config_element_by_flow_group_name',
                               return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                self.ixnet_gen.update_l4(TRAFFIC_PARAMETERS)

    def test_update_l4_exception_no_supported_proto(self):
        traffic_parameters = {
            UPLINK: {
                'id': 1,
                'outer_l3': {
                    'proto': 'unsupported',
                },
                'outer_l4': {
                    'seed': 1
                }
            },
        }
        with mock.patch.object(self.ixnet_gen,
                               '_get_config_element_by_flow_group_name',
                               return_value='celm'):
            with self.assertRaises(exceptions.IXIAUnsupportedProtocol):
                self.ixnet_gen.update_l4(traffic_parameters)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic(self, mock_ixnextgen_get_traffic_state):
        self.ixnet_gen._ixnet.getList.return_value = [0]

        mock_ixnextgen_get_traffic_state.side_effect = [
            'stopped', 'started', 'started', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(3, self.ixnet_gen._ixnet.execute.call_count)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic_traffic_running(
            self, mock_ixnextgen_get_traffic_state):
        self.ixnet_gen._ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'started', 'stopped', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(4, self.ixnet_gen._ixnet.execute.call_count)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic_wait_for_traffic_to_stop(
            self, mock_ixnextgen_get_traffic_state):
        self.ixnet_gen._ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'started', 'started', 'started', 'stopped', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(4, self.ixnet_gen._ixnet.execute.call_count)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic_wait_for_traffic_start(
            self, mock_ixnextgen_get_traffic_state):
        self.ixnet_gen._ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'stopped', 'stopped', 'stopped', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(3, self.ixnet_gen._ixnet.execute.call_count)

    def test_start_protocols(self):
        self.ixnet_gen.start_protocols()
        self.ixnet.execute.assert_called_once_with('startAllProtocols')

    def test_stop_protocols(self):
        self.ixnet_gen.stop_protocols()
        self.ixnet.execute.assert_called_once_with('stopAllProtocols')

    def test_get_vports(self):
        self.ixnet_gen._ixnet.getRoot.return_value = 'root'
        self.ixnet_gen.get_vports()
        self.ixnet.getList.assert_called_once_with('root', 'vport')
