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
            'framesize': {'64B': '25', '256B': '75'}
        },
        'outer_l3': {
            'count': 512,
            'dscp': 0,
            'proto': 'udp',
            'ttl': 32,
            'dstip': '152.16.40.20',
            'srcip': '152.16.100.20',
            'dstmask': 24,
            'srcmask': 24
        },
        'outer_l4': {
            'dstport': '2001',
            'srcport': '1234'
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
            'framesize': {'128B': '35', '1024B': '65'}
        },
        'outer_l3': {
            'count': 1024,
            'dscp': 0,
            'proto': 'udp',
            'ttl': 32,
            'dstip': '2001::10',
            'srcip': '2021::10',
            'dstmask': 64,
            'srcmask': 64
        },
        'outer_l4': {
            'dstport': '1234',
            'srcport': '2001'
        },
        'traffic_type': 'continuous'
    }
}


class TestIxNextgen(unittest.TestCase):

    def setUp(self):
        self.ixnet = mock.Mock()
        self.ixnet.execute = mock.Mock()
        self.ixnet.getRoot.return_value = 'my_root'

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
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.side_effect = [['traffic_item'],
                                                ['fg_01']]
        ixnet_gen._ixnet.getAttribute.return_value = 'flow_group_01'
        output = ixnet_gen._get_config_element_by_flow_group_name(
            'flow_group_01')
        self.assertEqual('traffic_item/configElement:flow_group_01', output)

    def test__get_config_element_by_flow_group_name_no_match(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.side_effect = [['traffic_item'],
                                                ['fg_01']]
        ixnet_gen._ixnet.getAttribute.return_value = 'flow_group_02'
        output = ixnet_gen._get_config_element_by_flow_group_name(
            'flow_group_01')
        self.assertIsNone(output)

    def test__get_stack_item(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = ['tcp1', 'tcp2', 'udp']
        with mock.patch.object(
                ixnet_gen, '_get_config_element_by_flow_group_name') as \
                mock_get_cfg_element:
            mock_get_cfg_element.return_value = 'cfg_element'
            output = ixnet_gen._get_stack_item(mock.ANY, ixnet_api.PROTO_TCP)
        self.assertEqual(['tcp1', 'tcp2'], output)

    def test__get_stack_item_no_config_element(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(
                ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                ixnet_gen._get_stack_item(mock.ANY, mock.ANY)

    def test__get_field_in_stack_item(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = ['field1', 'field2']
        output = ixnet_gen._get_field_in_stack_item(mock.ANY, 'field2')
        self.assertEqual('field2', output)

    def test__get_field_in_stack_item_no_field_present(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = ['field1', 'field2']
        with self.assertRaises(exceptions.IxNetworkFieldNotPresentInStackItem):
            ixnet_gen._get_field_in_stack_item(mock.ANY, 'field3')

    def test__parse_framesize(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        framesize = {'64B': '75', '512b': '25'}
        output = ixnet_gen._parse_framesize(framesize)
        self.assertEqual(2, len(output))
        self.assertIn([64, 64, 75], output)
        self.assertIn([512, 512, 25], output)

    @mock.patch.object(IxNetwork, 'IxNet')
    def test_connect(self, mock_ixnet):
        mock_ixnet.return_value = self.ixnet
        ixnet_gen = ixnet_api.IxNextgen()
        with mock.patch.object(ixnet_gen, 'get_config') as mock_config:
            mock_config.return_value = {'machine': 'machine_fake',
                                        'port': 'port_fake',
                                        'version': 12345}
            ixnet_gen.connect(mock.ANY)

        self.ixnet.connect.assert_called_once_with(
            'machine_fake', '-port', 'port_fake', '-version', '12345')
        mock_config.assert_called_once()

    def test_connect_invalid_config_no_machine(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.get_config = mock.Mock(return_value={
            'port': 'port_fake',
            'version': '12345'})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_invalid_config_no_port(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.get_config = mock.Mock(return_value={
            'machine': 'machine_fake',
            'version': '12345'})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_invalid_config_no_version(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.get_config = mock.Mock(return_value={
            'machine': 'machine_fake',
            'port': 'port_fake'})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_connect_no_config(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.get_config = mock.Mock(return_value={})
        self.assertRaises(KeyError, ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    def test_clear_config(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.clear_config()
        self.ixnet.execute.assert_called_once_with('newConfig')

    @mock.patch.object(ixnet_api, 'log')
    def test_assign_ports_2_ports(self, *args):
        self.ixnet.getAttribute.side_effect = ['up', 'down']
        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['2', '2']}
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._cfg = config

        self.assertIsNone(ixnet_gen.assign_ports())
        self.assertEqual(self.ixnet.execute.call_count, 2)
        self.assertEqual(self.ixnet.commit.call_count, 4)
        self.assertEqual(self.ixnet.getAttribute.call_count, 2)

    @mock.patch.object(ixnet_api, 'log')
    def test_assign_ports_port_down(self, mock_log):
        self.ixnet.getAttribute.return_value = 'down'
        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['3', '4']}
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._cfg = config
        ixnet_gen.assign_ports()
        mock_log.warning.assert_called()

    def test_assign_ports_no_config(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._cfg = {}
        self.assertRaises(KeyError, ixnet_gen.assign_ports)

    def test__create_traffic_item(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        self.ixnet.add.return_value = 'my_new_traffic_item'
        self.ixnet.remapIds.return_value = ['my_traffic_item_id']

        ixnet_gen._create_traffic_item()
        self.ixnet.add.assert_called_once_with(
            'my_root/traffic', 'trafficItem')
        self.ixnet.setMultiAttribute.assert_called_once_with(
            'my_new_traffic_item', '-name', 'RFC2544', '-trafficType', 'raw')
        self.assertEqual(2, self.ixnet.commit.call_count)
        self.ixnet.remapIds.assert_called_once_with('my_new_traffic_item')
        self.ixnet.setAttribute('my_traffic_item_id/tracking',
                                '-trackBy', 'trafficGroupId0')

    def test__create_flow_groups(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.ixnet.getList.side_effect = [['traffic_item'], ['1', '2']]
        ixnet_gen.ixnet.add.side_effect = ['endp1', 'endp2']
        ixnet_gen._create_flow_groups()
        ixnet_gen.ixnet.add.assert_has_calls([
            mock.call('traffic_item', 'endpointSet'),
            mock.call('traffic_item', 'endpointSet')])
        ixnet_gen.ixnet.setMultiAttribute.assert_has_calls([
            mock.call('endp1', '-name', '1', '-sources', ['1/protocols'],
                      '-destinations', ['2/protocols']),
            mock.call('endp2', '-name', '2', '-sources', ['2/protocols'],
                      '-destinations', ['1/protocols'])])

    def test__append_protocol_to_stack(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet

        ixnet_gen._append_procotol_to_stack('my_protocol', 'prev_element')
        self.ixnet.execute.assert_called_with(
            'append', 'prev_element',
            'my_root/traffic/protocolTemplate:"my_protocol"')

    def test__setup_config_elements(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.ixnet.getList.side_effect = [['traffic_item'],
                                               ['cfg_element']]
        with mock.patch.object(ixnet_gen, '_append_procotol_to_stack') as \
                mock_append_proto:
            ixnet_gen._setup_config_elements()
        mock_append_proto.assert_has_calls([
            mock.call(ixnet_api.PROTO_UDP, 'cfg_element/stack:"ethernet-1"'),
            mock.call(ixnet_api.PROTO_IPV4, 'cfg_element/stack:"ethernet-1"')])
        ixnet_gen.ixnet.setAttribute.assert_has_calls([
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
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet

        ixnet_gen.create_traffic_model()
        mock__create_traffic_item.assert_called_once()
        mock__create_flow_groups.assert_called_once()
        mock__setup_config_elements.assert_called_once()

    def test__update_frame_mac(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(ixnet_gen, '_get_field_in_stack_item') as \
                mock_get_field:
            mock_get_field.return_value = 'field_descriptor'
            ixnet_gen._update_frame_mac('ethernet_descriptor', 'field', 'mac')
        mock_get_field.assert_called_once_with('ethernet_descriptor', 'field')
        ixnet_gen.ixnet.setMultiAttribute(
            'field_descriptor', '-singleValue', 'mac', '-fieldValue', 'mac',
            '-valueType', 'singleValue')
        ixnet_gen.ixnet.commit.assert_called_once()

    def test_update_frame(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(
                ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value='cfg_element'), \
                mock.patch.object(ixnet_gen, '_update_frame_mac') as \
                mock_update_frame, \
                mock.patch.object(ixnet_gen, '_get_stack_item') as \
                mock_get_stack_item:
            mock_get_stack_item.side_effect = [['item1'], ['item2'],
                                               ['item3'], ['item4']]
            ixnet_gen.update_frame(TRAFFIC_PARAMETERS, 50)

        self.assertEqual(6, len(ixnet_gen.ixnet.setMultiAttribute.mock_calls))
        self.assertEqual(4, len(mock_update_frame.mock_calls))
        ixnet_gen.ixnet.setMultiAttribute.assert_has_calls(
            [mock.call('cfg_element/frameRate', '-rate', 10000.5,
                       '-type', 'framesPerSecond'),
             mock.call('cfg_element/frameRate', '-rate', 75.2, '-type',
                       'percentLineRate')],
            any_order=True)

    def test_update_frame_flow_not_present(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(
                ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                ixnet_gen.update_frame(TRAFFIC_PARAMETERS, 40)

    def test_get_statistics(self):
        ixnet_gen = ixnet_api.IxNextgen()
        port_statistics = '::ixNet::OBJ-/statistics/view:"Port Statistics"'
        flow_statistics = '::ixNet::OBJ-/statistics/view:"Flow Statistics"'
        with mock.patch.object(ixnet_gen, '_build_stats_map') as \
                mock_build_stats:
            ixnet_gen.get_statistics()

        mock_build_stats.assert_has_calls([
            mock.call(port_statistics, ixnet_gen.PORT_STATS_NAME_MAP),
            mock.call(flow_statistics, ixnet_gen.LATENCY_NAME_MAP)])

    def test__update_ipv4_address(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(ixnet_gen, '_get_field_in_stack_item',
                               return_value='field_desc'):
            ixnet_gen._update_ipv4_address(mock.ANY, mock.ANY, '192.168.1.1',
                                           100, 26, 25)
        ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'field_desc', '-seed', 100, '-fixedBits', '192.168.1.1',
            '-randomMask', '0.0.0.63', '-valueType', 'random',
            '-countValue', 25)

    def test_update_ip_packet(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(ixnet_gen, '_update_ipv4_address') as \
                mock_update_add, \
                mock.patch.object(ixnet_gen, '_get_stack_item'), \
                mock.patch.object(ixnet_gen,
                '_get_config_element_by_flow_group_name', return_value='celm'):
            ixnet_gen.update_ip_packet(TRAFFIC_PARAMETERS)

        self.assertEqual(4, len(mock_update_add.mock_calls))

    def test_update_ip_packet_exception_no_config_element(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(ixnet_gen,
                               '_get_config_element_by_flow_group_name',
                               return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                ixnet_gen.update_ip_packet(TRAFFIC_PARAMETERS)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic(self, mock_ixnextgen_get_traffic_state):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = [0]

        mock_ixnextgen_get_traffic_state.side_effect = [
            'stopped', 'started', 'started', 'started']

        result = ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(3, ixnet_gen._ixnet.execute.call_count)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic_traffic_running(
            self, mock_ixnextgen_get_traffic_state):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'started', 'stopped', 'started']

        result = ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(4, ixnet_gen._ixnet.execute.call_count)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic_wait_for_traffic_to_stop(
            self, mock_ixnextgen_get_traffic_state):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'started', 'started', 'started', 'stopped', 'started']

        result = ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(4, ixnet_gen._ixnet.execute.call_count)

    @mock.patch.object(ixnet_api.IxNextgen, '_get_traffic_state')
    def test_start_traffic_wait_for_traffic_start(
            self, mock_ixnextgen_get_traffic_state):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'stopped', 'stopped', 'stopped', 'started']

        result = ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(3, ixnet_gen._ixnet.execute.call_count)
