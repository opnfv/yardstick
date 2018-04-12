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
import IxNetwork
import unittest

from yardstick.common import exceptions
from yardstick.network_services.libs.ixia_libs.IxNet import IxNet
from yardstick.network_services.libs.ixia_libs.IxNet.IxNet import IxNextgen

UPLINK = "uplink"
DOWNLINK = "downlink"


class TestIxNextgen(unittest.TestCase):

    def setUp(self):
        self.ixnet = mock.Mock()
        self.ixnet.execute = mock.Mock()
        self.ixnet_gen = IxNextgen()
        self.ixnet_gen._ixnet = self.ixnet

    def test_get_config(self):
        tg_cfg = {
            "vdu": [
                {
                    "external-interface": [
                        {
                            "virtual-interface": {
                                "vpci": "0000:07:00.1",
                            },
                        },
                        {
                            "virtual-interface": {
                                "vpci": "0001:08:01.2",
                            },
                        },
                    ],
                },
            ],
            "mgmt-interface": {
                "ip": "test1",
                "tg-config": {
                    "dut_result_dir": "test2",
                    "version": "test3",
                    "ixchassis": "test4",
                    "tcl_port": "test5",
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

        result = IxNextgen.get_config(tg_cfg)
        self.assertEqual(result, expected)

    def test___init__(self):
        ixnet_gen = IxNextgen()
        with self.assertRaises(exceptions.IxNetworkClientNotConnected):
            ixnet_gen.ixnet  # pylint: disable=pointless-statement
        self.assertTrue(isinstance(ixnet_gen._objRefs, dict))
        self.assertIsNone(ixnet_gen._cfg)
        self.assertIsNone(ixnet_gen._params)
        self.assertIsNone(ixnet_gen._bidir)

    def test___init__ixnet(self):
        # test when initialised with ixnet as a param
        self.assertIsNotNone(self.ixnet_gen.ixnet)
        self.assertTrue(isinstance(self.ixnet_gen._objRefs, dict))
        self.assertIsNone(self.ixnet_gen._cfg)
        self.assertIsNone(self.ixnet_gen._params)
        self.assertIsNone(self.ixnet_gen._bidir)

    #ELF
    def test_ixnet(self):
        pass

    #ELF
    def test_ixnet_unset(self):
        pass

    #ELF
    def test__get_config_element_by_flow_group_name(self):
        pass

    #ELF3
    def test__get_stack_item(self):
        pass

    #ELF3
    def test__get_stack_item_exception_flow_not_present(self):
        # get_config_element_by_flow_group returns None?
        pass

    #ELF2
    #ELF3
    def test__get_field_in_stack_item(self):
        pass

    #ELF3
    def test__get_field_in_stack_item_exception_fiel_not_present(self):
        pass

    #ELF4
    def test__get_traffic_state(self):
        pass

    #ELF4
    def test_is_traffic_running(self):
        pass

    #ELF4
    def test_is_traffic_running_traffic_stopped(self):
        pass

    #ELF4
    def test_is_traffic_stopped(self):
        pass

    #ELF4
    def test_is_traffic_stopped_traffic_running(self):
        pass

    #ELF
    def test__parse_framesize(self):
        pass

    #ELF1: Do I need more tests??
    @mock.patch.object(IxNetwork, 'IxNet')
    def test_connect(self, mock_ixnet):
        mock_ixnet.return_value = self.ixnet
        ixnet_gen = IxNextgen()
        with mock.patch.object(ixnet_gen, 'get_config') as mock_config:
            mock_config.return_value = {'machine': 'machine_fake',
                                        'port': 'port_fake',
                                        'version': 12345}
            output = ixnet_gen.connect(mock.ANY)

        self.ixnet.connect.assert_called_once_with(
            'machine_fake', '-port', 'port_fake', '-version', '12345')
        mock_config.assert_called_once()
        self.assertIsNotNone(output)

    #ELF1
    def test_connect_invalid_config_no_machine(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={
            "port": "port_fake",
            "version": "12345" })
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    #ELF1
    def test_connect_invalid_config_no_port(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={
            "machine": "machine_fake",
            "version": "12345" })
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    #ELF1
    def test_connect_invalid_config_no_version(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={
            "machine": "machine_fake",
            "port": "port_fake"})
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    #ELF1
    def test_connect_no_config(self):
        self.ixnet_gen.get_config = mock.Mock(return_value={})
        self.assertRaises(KeyError, self.ixnet_gen.connect, mock.ANY)
        self.ixnet.connect.assert_not_called()

    # ELF1: ixnet could be an instance variable for the testcase, so it would
    # always be set up and available.
    def test_clear_config(self):
        self.ixnet_gen.clear_config()

        self.ixnet.execute.assert_called_once_with('newConfig')

    # ELF1: Need to add more tests for assign_ports
    # ELF1: mock using mock.patch.object
    # ELF1: Need to add test for multiple ports and multiple calls to execute
    def test_assign_ports(self):
        self.ixnet.getAttribute.side_effect = ['up']

        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['1', ],
        }

        self.ixnet_gen._cfg = config

        self.assertIsNone(self.ixnet_gen.assign_ports())

        self.ixnet.execute.assert_called_once()
        self.assertEqual(self.ixnet.commit.call_count, 2)
        self.ixnet.getAttribute.assert_called_once()

    def test_assign_ports_2_ports(self):
        self.ixnet.getAttribute.side_effect = ['up', 'down']

        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['2', '2'],
        }

        self.ixnet_gen._cfg = config

        self.assertIsNone(self.ixnet_gen.assign_ports())

        self.assertEqual(self.ixnet.execute.call_count, 2)
        self.assertEqual(self.ixnet.commit.call_count, 4)
        self.assertEqual(self.ixnet.getAttribute.call_count, 2)

    #ELF
    @mock.patch.object(IxNet, 'log')
    def test_assign_ports_port_down(self, mock_log):
        self.ixnet.getAttribute.return_value = 'down'
        config = {
            'chassis': '1.1.1.1',
            'cards': ['1', '2'],
            'ports': ['3', '4'],
        }
        self.ixnet_gen._cfg = config

        self.ixnet_gen.assign_ports()

        mock_log.warning.assert_called()

    # ELF1
    def test_assign_ports_no_config(self):
        self.ixnet_gen._cfg = {}

        self.assertRaises(KeyError, self.ixnet_gen.assign_ports)

    #ELF1
    def test__create_traffic_item(self):
        self.ixnet.getRoot.return_value = "rootyrootroot"
        self.ixnet.add.return_value = "my_new_traffic_item"
        self.ixnet.remapIds.return_value = ["my_traffic_item_id"]

        self.ixnet_gen._create_traffic_item()

        self.ixnet.add.assert_called_once_with(
            "rootyrootroot/traffic",
            "trafficItem")
        self.ixnet.setMultiAttribute.assert_called_once_with(
            "my_new_traffic_item", "-name", "RFC2544", "-trafficType", "raw"
        )
        self.assertEqual(2, self.ixnet.commit.call_count)
        self.ixnet.remapIds.assert_called_once_with("my_new_traffic_item")
        self.ixnet.setAttribute("my_traffic_item_id/tracking",
                                "-trackBy", "trafficGroupId0")

    def test__create_flow_groups(self):
        #ELF1: implement me!
        # Single group
        pass

    #ELF1
    def test__create_flow_groups_multiple_groups(self):
        pass

    #ELF1
    def test__create_flow_groups_no_traffic_item(self):
        # we should not enter the for loop;
        # ixnet.execute/setAttribute should not be called
        pass

    #ELF1
    def test__create_flow_groups_no_ports(self):
        # this tc should actually throw an error because we try
        # to acess the vports
        pass

    #ELF1
    def test__append_protocol_to_stack(self):
        self.ixnet.getRoot.return_value = "my_root"
        previous_element = "prev_element"

        self.ixnet_gen._append_procotol_to_stack('my_protocol', 'prev_element')
        self.ixnet.execute.assert_called_with(
            'append',
            'prev_element',
            'my_root/traffic/protocolTemplate:"my_protocol"'
            )

    #ELF1
    def test__setup_config_elements(self):
        #ELF1: implement me!
        pass

    #ELF1
    def test__setup_config_elements_no_traffic_item(self):
        # How does ixnet react when given a null traffic item?
        pass

    #ELF1
    def test__setup_config_elements_no_config(self):
        # getList returns None for configElement
        pass

    #ELF1
    @mock.patch.object(IxNextgen, "_create_traffic_item") 
    @mock.patch.object(IxNextgen, "_create_flow_groups") 
    @mock.patch.object(IxNextgen, "_setup_config_elements") 
    def test_create_traffic_model(self, mock__setup_config_elements,
                                  mock__create_flow_groups,
                                  mock__create_traffic_item):
        self.ixnet_gen.create_traffic_model()

        mock__create_traffic_item.assert_called_once()
        mock__create_flow_groups.assert_called_once()
        mock__setup_config_elements.assert_called_once()
        # ELF1: Check for side effects

    #ELF2
    def test__update_frame_mac(self):
        pass

    #ELF3:
    def test__update_ipv4_address(self):
        # generate a valid return value for get_field_in_stack_item
        # make sure ixnet.setMultiAttribute is called
        # make sure ixnet.commit is called
        # sample params are in Ixnet class called by update_ip_packet
        pass

    #ELF3:
    def test__update_ipv4_address_exception_field_not_found(self):
        # get_field_in_stack_item throws an error
        pass

    #ELF3
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
    #ELF3
    def test_update_ip_packet_exception_no_config_element(self):
        # _get_config_element_by_flow returns None
        # traffic = ??
        # self.assertRaises(exceptions.IxNetworkFlowNotPresent,
        # ixNetgen.update_ip_packet(traffic))
        # Is the traffic param mutated? If so, check that, else check that
        # update_ipv4_address is called with the right params

        # make sure that get_config_element is called for each param in the traffic dict
        pass

    # ELF: need some negative testing for this method
    # ELF: Also check for the new change to this funct
    #  -- should fail for traffic type = continuous
    # ELF: Why is this failing? The element exists
    def test_update_frame(self):
        static_traffic_params = {
            UPLINK: {
                "id": 1,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:03",
                    "framesPerSecond": True,
                    "framesize": {
                        "64B": "100",
                        "1KB": "0",
                    },
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "dscp": 0,
                    "dstip4": "152.16.40.20",
                    "proto": "udp",
                    "srcip4": "152.16.100.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "2001",
                    "srcport": "1234"
                },
                "traffic_type": "continuous"
            },
            DOWNLINK: {
                "id": 2,
                "bidir": "False",
                "duration": 60,
                "iload": "100",
                "outer_l2": {
                    "dstmac": "00:00:00:00:00:04",
                    "framesPerSecond": False,
                    "framesize": {"64B": "100"},
                    "srcmac": "00:00:00:00:00:01"
                },
                "outer_l3": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v4": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l3v6": {
                    "count": 1024,
                    "dscp": 0,
                    "dstip4": "152.16.100.20",
                    "proto": "udp",
                    "srcip4": "152.16.40.20",
                    "ttl": 32
                },
                "outer_l4": {
                    "dstport": "1234",
                    "srcport": "2001"
                },
                "traffic_type": "continuous"
            }
        }

        self.ixnet.remapIds.return_value = ["0"]
        self.ixnet.setMultiAttribute.return_value = [1]
        self.ixnet.commit.return_value = [1]
        self.ixnet.getRoot.return_value = ""
        self.ixnet.getList.return_value = [
            [1],
            [1],
            [1],
            [
                "ethernet.header.destinationAddress",
                "ethernet.header.sourceAddress",
            ],
        ]

        result = self.ixnet_gen.update_frame(static_traffic_params)
        self.assertIsNone(result)
        self.assertEqual(self.ixnet.setMultiAttribute.call_count, 7)
        self.assertEqual(self.ixnet.commit.call_count, 2)

    #ELF1: these might be removed in a later petchset, check this!!
    def test_update_ether_multi_attribute(self):
        pass

    #ELF1: where were there update_ether functions used?
    # are they still needed?
    def test_update_ether_multi_attributes(self):
        pass

    #ELF: more tests for Rodolfo's changes!
    @mock.patch.object(IxNextgen, '_get_traffic_state')
    def test_start_traffic(self, mock_ixnextgen_get_traffic_state):
        self.ixnet.getList.return_value = [0]

        mock_ixnextgen_get_traffic_state.side_effect = [
            'stopped', 'started', 'started', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(self.ixnet.execute.call_count, 3)

    #ELF4
    @mock.patch.object(IxNextgen, '_get_traffic_state')
    def test_start_traffic_traffic_running(
            self, mock_ixnextgen_get_traffic_state):
        self.ixnet.getList.return_value = [0]
        ixnet_gen = IxNextgen()
        ixnet_gen._ixnet = self.ixnet
        mock_ixnextgen_get_traffic_state.side_effect = [
            'started', 'stopped', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(self.ixnet.execute.call_count, 4)

    #ELF4
    @mock.patch.object(IxNextgen, '_get_traffic_state')
    def test_start_traffic_wait_for_traffic_to_stop(
            self, mock_ixnextgen_get_traffic_state):
        self.ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'started', 'started', 'started', 'stopped', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(self.ixnet.execute.call_count, 4)

    # ELF4
    @mock.patch.object(IxNextgen, '_get_traffic_state')
    def test_start_traffic_wait_for_traffic_start(
            self, mock_ixnextgen_get_traffic_state):
        self.ixnet.getList.return_value = [0]
        mock_ixnextgen_get_traffic_state.side_effect = [
            'stopped', 'stopped', 'stopped', 'started']

        result = self.ixnet_gen.start_traffic()
        self.assertIsNone(result)
        self.ixnet.getList.assert_called_once()
        self.assertEqual(self.ixnet.execute.call_count, 3)

    #ELF1
    def test_build_stats_map(self):
        pass

    #ELF4
    # ELF: Needs a rename
    # ELF: Needs more tests!
    def test_get_statistics(self):
        self.ixnet.execute.return_value = ""

        result = self.ixnet_gen.get_statistics()
        self.assertIsNotNone(result)
        self.assertEqual(self.ixnet.execute.call_count, 12)

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
