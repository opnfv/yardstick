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
        'iload': '100',
        'outer_l2': {
            'framesize': {'64B': '25', '256B': '75'}
        },
        'outer_l3': {
            'dscp': 0,
            'dstip4': '152.16.40.20',
            'proto': 'udp',
            'srcip4': '152.16.100.20',
            'ttl': 32
        },
        'outer_l3v4': {
            'dscp': 0,
            'dstip4': '152.16.40.20',
            'proto': 'udp',
            'srcip4': '152.16.100.20',
            'ttl': 32
        },
        'outer_l3v6': {
            'count': 1024,
            'dscp': 0,
            'dstip4': '152.16.100.20',
            'proto': 'udp',
            'srcip4': '152.16.40.20',
            'ttl': 32
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
        'iload': '100',
        'outer_l2': {
            'framesize': {'128B': '35', '1024B': '65'}
        },
        'outer_l3': {
            'count': 1024,
            'dscp': 0,
            'dstip4': '152.16.100.20',
            'proto': 'udp',
            'srcip4': '152.16.40.20',
            'ttl': 32
        },
        'outer_l3v4': {
            'count': 1024,
            'dscp': 0,
            'dstip4': '152.16.100.20',
            'proto': 'udp',
            'srcip4': '152.16.40.20',
            'ttl': 32
        },
        'outer_l3v6': {
            'count': 1024,
            'dscp': 0,
            'dstip4': '152.16.100.20',
            'proto': 'udp',
            'srcip4': '152.16.40.20',
            'ttl': 32
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

    def test__parse_framesize(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        framesize = {'64B': '75', '512b': '25'}
        output = ixnet_gen._parse_framesize(framesize)
        for idx in range(len(framesize)):
            if output[idx * 2] == 64:
                self.assertEqual(75, output[idx * 2 + 1])
            elif output[idx * 2] == 512:
                self.assertEqual(25, output[idx * 2 + 1])
            else:
                raise self.failureException('Framesize (64, 512) not present')

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

    def test__get_field_in_stack_item(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = ['field1', 'field2']
        output = ixnet_gen._get_field_in_stack_item(mock.ANY, 'field2')
        self.assertEqual('field2', output)

    def test__get_field_in_stack_item_field_not_present(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._ixnet.getList.return_value = ['field1', 'field2']
        with self.assertRaises(exceptions.IxNetworkFieldNotPresentInStackItem):
            ixnet_gen._get_field_in_stack_item(mock.ANY, 'field3')

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

    # RAH
    # self._get_stack_item(fg_id, PROTO_ETHERNET)[0],

    def test_update_frame(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(
                ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value='cfg_element'), \
                mock.patch.object(ixnet_gen, '_update_frame_mac') as \
                mock_update_frame:
            ixnet_gen.update_frame(TRAFFIC_PARAMETERS)

        self.assertEqual(6, len(ixnet_gen.ixnet.setMultiAttribute.mock_calls))
        self.assertEqual(4, len(mock_update_frame.mock_calls))

    def test_update_frame_flow_not_present(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        with mock.patch.object(
                ixnet_gen, '_get_config_element_by_flow_group_name',
                return_value=None):
            with self.assertRaises(exceptions.IxNetworkFlowNotPresent):
                ixnet_gen.update_frame(TRAFFIC_PARAMETERS)





    def test_set_random_ip_multi_attribute(self):
        ixnet_gen = ixnet_api.IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen.set_random_ip_multi_attribute('ipv4', 20, 30, 40, 100)
        ixnet_gen.ixnet.setMultiAttribute.assert_called_once_with(
            'ipv4', '-seed', '20', '-fixedBits', '30', '-randomMask', '40',
            '-valueType', 'random', '-countValue', '100')

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




    # def _update_ipv4_address(self, ip_descriptor, field, ip_address, seed,
    #                          mask, count):
    #     """Set the IPv4 address in a config element stack IP field
    #
    #     :param ip_descriptor: (str) IP descriptor, e.g.:
    #         /traffic/trafficItem:1/configElement:1/stack:"ipv4-2"
    #     :param field: (str) field name, e.g.: scrIp, dstIp
    #     :param ip_address: (str) IP address
    #     :param seed: (int) seed length
    #     :param mask: (str) IP address mask
    #     :param count: (int) number of random IPs to generate
    #     """
    #     field_descriptor = self._get_field_in_stack_item(ip_descriptor,
    #                                                      field)
    #     self.ixnet.setMultiAttribute(field_descriptor,
    #                                  '-seed', seed,
    #                                  '-fixedBits', ip_address,
    #                                  '-randomMask', mask,
    #                                  '-valueType', 'random',
    #                                  '-countValue', count)

    #ELF3: Need positive tests??
    #ELF3: Check that params are correct
    def test__update_ipv4_address_bad_ip_version(self):
        bad_ip_version = ""

        ixnet_gen = IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        ixnet_gen._get_field_in_stack_item = mock.Mock()
        ixnet_gen._get_field_in_stack_item.side_effect = \
            exceptions.IxNetworkFieldNotPresentInStackItem

        with self.assertRaises(exceptions.IxNetworkFieldNotPresentInStackItem):
            ixnet_gen._update_ipv4_address(
                ip_descriptor=bad_ip_version, field="srcIp", ip_address=mock.Mock(),
                seed=mock.Mock(), mask=mock.Mock(), count=mock.Mock())
            self.ixnet.setMultiAttribute.assert_not_called()



    #RAH
    # def update_ip_packet(self, traffic):
    #     """Update the IP packet
    #
    #     NOTE: Only IPv4 is currently supported.
    #     :param traffic: list of traffic elements; each traffic element contains
    #                     the injection parameter for each flow group.
    #     """
    #     # NOTE(ralonsoh): L4 configuration is not set.
    #     for traffic_param in traffic.values():
    #         fg_id = str(traffic_param['id'])
    #         config_element = self._get_config_element_by_flow_group_name(
    #             fg_id)
    #         if not config_element:
    #             raise exceptions.IxNetworkFlowNotPresent(
    #                 flow_group=fg_id)
    #
    #         count = traffic_param['outer_l3']['count']
    #         srcip4 = str(traffic_param['outer_l3']['srcip4'])
    #         dstip4 = str(traffic_param['outer_l3']['dstip4'])
    #
    #         self._update_ipv4_address(
    #             self._get_stack_item(fg_id, PROTO_IPV4)[0],
    #             'srcIp', srcip4, 1, IP_VERSION_4_MASK, count)
    #         self._update_ipv4_address(
    #             self._get_stack_item(fg_id, PROTO_IPV4)[0],
    #             'dstIp', dstip4, 1, IP_VERSION_4_MASK, count)

            # ELF3

    def test_update_ip_packet(self):
        # create valid traffic param
        traffic = {  # pylint: disable=unused-variable
            "uplink": {
                "id": 1,
                "outer_l3": {
                    "count": 1,
                    "srcip4": "10.10.10.10",
                    "dstip4": "11.11.11.11",
                }
            }
        }
        # ELF3

    def test_update_ip_packet_exception_no_config_element(self):
        # _get_config_element_by_flow returns None
        # traffic = ??
        # self.assertRaises(exceptions.IxNetworkFlowNotPresent,
        # ixNetgen.update_ip_packet(traffic))
        # Is the traffic param mutated? If so, check that, else check that
        # update_ipv4_address is called with the right params

        # make sure that get_config_element is called for each param in the traffic dict
        pass
