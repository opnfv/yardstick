# Copyright (c) 2016-2018 Intel Corporation
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
import logging

import IxNetwork

from yardstick.common import exceptions
from yardstick.common import utils
from yardstick.network_services.traffic_profile import base as tp_base


log = logging.getLogger(__name__)

IP_VERSION_4 = 4
IP_VERSION_6 = 6

PROTO_ETHERNET = 'ethernet'
PROTO_IPV4 = 'ipv4'
PROTO_IPV6 = 'ipv6'
PROTO_UDP = 'udp'
PROTO_TCP = 'tcp'
PROTO_VLAN = 'vlan'

SINGLE_VALUE = "singleValue"

S_VLAN = 0
C_VLAN = 1

ETHER_TYPE_802_1ad = '0x88a8'

IP_VERSION_4_MASK = 24
IP_VERSION_6_MASK = 64

TRAFFIC_STATUS_STARTED = 'started'
TRAFFIC_STATUS_STOPPED = 'stopped'

SUPPORTED_PROTO = [PROTO_UDP]


class Vlan(object):
    def __init__(self,
                 vlan_id, vlan_id_step=None, vlan_id_direction='increment',
                 prio=None, prio_step=None, prio_direction='increment',
                 tp_id=None):
        self.vlan_id = vlan_id
        self.vlan_id_step = vlan_id_step
        self.vlan_id_direction = vlan_id_direction
        self.prio = prio
        self.prio_step = prio_step
        self.prio_direction = prio_direction
        self.tp_id = tp_id


# NOTE(ralonsoh): this pragma will be removed in the last patch of this series
class IxNextgen(object):  # pragma: no cover

    PORT_STATS_NAME_MAP = {
        "stat_name": 'Stat Name',
        "Frames_Tx": 'Frames Tx.',
        "Valid_Frames_Rx": 'Valid Frames Rx.',
        "Frames_Tx_Rate": 'Frames Tx. Rate',
        "Valid_Frames_Rx_Rate": 'Valid Frames Rx. Rate',
        "Tx_Rate_Kbps": 'Tx. Rate (Kbps)',
        "Rx_Rate_Kbps": 'Rx. Rate (Kbps)',
        "Tx_Rate_Mbps": 'Tx. Rate (Mbps)',
        "Rx_Rate_Mbps": 'Rx. Rate (Mbps)',
    }

    LATENCY_NAME_MAP = {
        "Store-Forward_Avg_latency_ns": 'Store-Forward Avg Latency (ns)',
        "Store-Forward_Min_latency_ns": 'Store-Forward Min Latency (ns)',
        "Store-Forward_Max_latency_ns": 'Store-Forward Max Latency (ns)',
    }

    @staticmethod
    def get_config(tg_cfg):
        card = []
        port = []
        external_interface = tg_cfg["vdu"][0]["external-interface"]
        for intf in external_interface:
            card_port0 = intf["virtual-interface"]["vpci"]
            card0, port0 = card_port0.split(':')[:2]
            card.append(card0)
            port.append(port0)

        cfg = {
            'machine': tg_cfg["mgmt-interface"]["ip"],
            'port': tg_cfg["mgmt-interface"]["tg-config"]["tcl_port"],
            'chassis': tg_cfg["mgmt-interface"]["tg-config"]["ixchassis"],
            'cards': card,
            'ports': port,
            'output_dir': tg_cfg["mgmt-interface"]["tg-config"]["dut_result_dir"],
            'version': tg_cfg["mgmt-interface"]["tg-config"]["version"],
            'bidir': True,
        }

        return cfg

    def __init__(self):  # pragma: no cover
        self._ixnet = None
        self._cfg = None
        self._params = None
        self._bidir = None

    @property
    def ixnet(self):  # pragma: no cover
        if self._ixnet:
            return self._ixnet
        raise exceptions.IxNetworkClientNotConnected()

    def get_vports(self):
        """Return the list of assigned ports (vport objects)"""
        vports = self.ixnet.getList(self.ixnet.getRoot(), 'vport')
        return vports

    def _get_config_element_by_flow_group_name(self, flow_group_name):
        """Get a config element using the flow group name

        Each named flow group contains one config element (by configuration).
        According to the documentation, "configElements" is a list and "each
        item in this list is aligned to the sequential order of your endpoint
        list".

        :param flow_group_name: (str) flow group name; this parameter is
                                always a number (converted to string) starting
                                from "1".
        :return: (str) config element reference ID or None.
        """
        traffic_item = self.ixnet.getList(self.ixnet.getRoot() + '/traffic',
                                          'trafficItem')[0]
        flow_groups = self.ixnet.getList(traffic_item, 'endpointSet')
        for flow_group in flow_groups:
            if (str(self.ixnet.getAttribute(flow_group, '-name')) ==
                    flow_group_name):
                return traffic_item + '/configElement:' + flow_group_name

    def _get_stack_item(self, flow_group_name, protocol_name):
        """Return the stack item given the flow group name and the proto name

        :param flow_group_name: (str) flow group name
        :param protocol_name: (str) protocol name, referred to PROTO_*
                              constants
        :return: list of stack item descriptors
        """
        celement = self._get_config_element_by_flow_group_name(flow_group_name)
        if not celement:
            raise exceptions.IxNetworkFlowNotPresent(
                flow_group=flow_group_name)
        stack_items = self.ixnet.getList(celement, 'stack')
        return [s_i for s_i in stack_items if protocol_name in s_i]

    def _get_field_in_stack_item(self, stack_item, field_name):
        """Return the field in a stack item given the name

        :param stack_item: (str) stack item descriptor
        :param field_name: (str) field name
        :return: (str) field descriptor
        """
        fields = self.ixnet.getList(stack_item, 'field')
        for field in (field for field in fields if field_name in field):
            return field
        raise exceptions.IxNetworkFieldNotPresentInStackItem(
            field_name=field_name, stack_item=stack_item)

    def _get_traffic_state(self):
        """Get traffic state"""
        return self.ixnet.getAttribute(self.ixnet.getRoot() + 'traffic',
                                       '-state')

    def is_traffic_running(self):
        """Returns true if traffic state == TRAFFIC_STATUS_STARTED"""
        return self._get_traffic_state() == TRAFFIC_STATUS_STARTED

    def is_traffic_stopped(self):
        """Returns true if traffic state == TRAFFIC_STATUS_STOPPED"""
        return self._get_traffic_state() == TRAFFIC_STATUS_STOPPED

    @staticmethod
    def _parse_framesize(framesize):
        """Parse "framesize" config param. to return a list of weighted pairs

        :param framesize: dictionary of frame sizes and weights
        :return: list of paired frame sizes and weights
        """
        weighted_range_pairs = []
        for size, weight in ((s, w) for (s, w) in framesize.items()
                             if int(w) != 0):
            size = int(size.upper().replace('B', ''))
            weighted_range_pairs.append([size, size, int(weight)])
        return weighted_range_pairs

    def iter_over_get_lists(self, x1, x2, y2, offset=0):
        for x in self.ixnet.getList(x1, x2):
            y_list = self.ixnet.getList(x, y2)
            for i, y in enumerate(y_list, offset):
                yield x, y, i

    def connect(self, tg_cfg):
        self._cfg = self.get_config(tg_cfg)
        self._ixnet = IxNetwork.IxNet()

        machine = self._cfg['machine']
        port = str(self._cfg['port'])
        version = str(self._cfg['version'])
        return self.ixnet.connect(machine, '-port', port,
                                  '-version', version)

    def clear_config(self):
        """Wipe out any possible configuration present in the client"""
        self.ixnet.execute('newConfig')

    def assign_ports(self):
        """Create and assign vports for each physical port defined in config

        This configuration is present in the IXIA profile file. E.g.:
            name: trafficgen_1
            role: IxNet
            interfaces:
                xe0:
                    vpci: "2:15" # Card:port
                    driver: "none"
                    dpdk_port_num: 0
                    local_ip: "152.16.100.20"
                    netmask: "255.255.0.0"
                    local_mac: "00:98:10:64:14:00"
                xe1:
                    ...
        """
        chassis_ip = self._cfg['chassis']
        ports = [(chassis_ip, card, port) for card, port in
                 zip(self._cfg['cards'], self._cfg['ports'])]

        log.info('Create and assign vports: %s', ports)

        vports = []
        for _ in ports:
            vports.append(self.ixnet.add(self.ixnet.getRoot(), 'vport'))
            self.ixnet.commit()

        self.ixnet.execute('assignPorts', ports, [], vports, True)
        self.ixnet.commit()

        for vport in vports:
            if self.ixnet.getAttribute(vport, '-state') != 'up':
                log.warning('Port %s is down', vport)

    def _create_traffic_item(self, traffic_type='raw'):
        """Create the traffic item to hold the flow groups

        The traffic item tracking by "Traffic Item" is enabled to retrieve the
        latency statistics.
        """
        log.info('Create the traffic item "RFC2544"')
        traffic_item = self.ixnet.add(self.ixnet.getRoot() + '/traffic',
                                      'trafficItem')
        self.ixnet.setMultiAttribute(traffic_item, '-name', 'RFC2544',
                                     '-trafficType', traffic_type)
        self.ixnet.commit()

        traffic_item_id = self.ixnet.remapIds(traffic_item)[0]
        self.ixnet.setAttribute(traffic_item_id + '/tracking',
                                '-trackBy', 'trafficGroupId0')
        self.ixnet.commit()

    def _create_flow_groups(self, uplink, downlink):
        """Create the flow groups between the endpoints"""
        traffic_item_id = self.ixnet.getList(self.ixnet.getRoot() + 'traffic',
                                             'trafficItem')[0]
        log.info('Create the flow groups')

        index = 0
        for up, down in zip(uplink, downlink):
            log.info('FGs: %s <--> %s', up, down)
            endpoint_set_1 = self.ixnet.add(traffic_item_id, 'endpointSet')
            endpoint_set_2 = self.ixnet.add(traffic_item_id, 'endpointSet')
            self.ixnet.setMultiAttribute(
                endpoint_set_1, '-name', str(index + 1),
                '-sources', [up],
                '-destinations', [down])
            self.ixnet.setMultiAttribute(
                endpoint_set_2, '-name', str(index + 2),
                '-sources', [down],
                '-destinations', [up])
            self.ixnet.commit()
            index += 2

    def _append_procotol_to_stack(self, protocol_name, previous_element):
        """Append a new element in the packet definition stack"""
        protocol = (self.ixnet.getRoot() +
                    '/traffic/protocolTemplate:"{}"'.format(protocol_name))
        self.ixnet.execute('append', previous_element, protocol)

    def _setup_config_elements(self, add_default_proto=True):
        """Setup the config elements

        The traffic item is configured to allow individual configurations per
        config element. The default frame configuration is applied:
            Ethernet II: added by default
            IPv4: element to add
            UDP: element to add
            Payload: added by default
            Ethernet II (Trailer): added by default
        :return:
        """
        traffic_item_id = self.ixnet.getList(self.ixnet.getRoot() + 'traffic',
                                             'trafficItem')[0]
        log.info('Split the frame rate distribution per config element')
        config_elements = self.ixnet.getList(traffic_item_id, 'configElement')
        for config_element in config_elements:
            self.ixnet.setAttribute(config_element + '/frameRateDistribution',
                                    '-portDistribution', 'splitRateEvenly')
            self.ixnet.setAttribute(config_element + '/frameRateDistribution',
                                    '-streamDistribution', 'splitRateEvenly')
            self.ixnet.commit()
            if add_default_proto:
                self._append_procotol_to_stack(
                    PROTO_UDP, config_element + '/stack:"ethernet-1"')
                self._append_procotol_to_stack(
                    PROTO_IPV4, config_element + '/stack:"ethernet-1"')

    def create_traffic_model(self, uplink_ports, downlink_ports):
        """Create a traffic item and the needed flow groups

        Each flow group inside the traffic item (only one is present)
        represents the traffic between two ports:
                        (uplink)    (downlink)
            FlowGroup1: port1    -> port2
            FlowGroup2: port1    <- port2
            FlowGroup3: port3    -> port4
            FlowGroup4: port3    <- port4
        """
        self._create_traffic_item('raw')
        uplink_endpoints = [port + '/protocols' for port in uplink_ports]
        downlink_endpoints = [port + '/protocols' for port in downlink_ports]
        self._create_flow_groups(uplink_endpoints, downlink_endpoints)
        self._setup_config_elements()

    def create_ipv4_traffic_model(self, uplink_topologies, downlink_topologies):
        """Create a traffic item and the needed flow groups

        Each flow group inside the traffic item (only one is present)
        represents the traffic between two topologies:
                        (uplink)    (downlink)
            FlowGroup1: uplink1    -> downlink1
            FlowGroup2: uplink1    <- downlink1
            FlowGroup3: uplink2    -> downlink2
            FlowGroup4: uplink2    <- downlink2
        """
        self._create_traffic_item('ipv4')
        self._create_flow_groups(uplink_topologies, downlink_topologies)
        self._setup_config_elements(False)

    def _update_frame_mac(self, ethernet_descriptor, field, mac_address):
        """Set the MAC address in a config element stack Ethernet field

        :param ethernet_descriptor: (str) ethernet descriptor, e.g.:
            /traffic/trafficItem:1/configElement:1/stack:"ethernet-1"
        :param field: (str) field name, e.g.: destinationAddress
        :param mac_address: (str) MAC address
        """
        field_descriptor = self._get_field_in_stack_item(ethernet_descriptor,
                                                         field)
        self.ixnet.setMultiAttribute(field_descriptor,
                                     '-singleValue', mac_address,
                                     '-fieldValue', mac_address,
                                     '-valueType', 'singleValue')
        self.ixnet.commit()

    def update_frame(self, traffic, duration):
        """Update the L2 frame

        This function updates the L2 frame options:
        - Traffic type: "continuous", "fixedDuration".
        - Duration: in case of traffic_type="fixedDuration", amount of seconds
                    to inject traffic.
        - Rate: in frames per seconds or percentage.
        - Type of rate: "framesPerSecond" or "percentLineRate" ("bitsPerSecond"
                         no used)
        - Frame size: custom IMIX [1] definition; a list of packet size in
                      bytes and the weight. E.g.:
                      [[64, 64, 10], [128, 128, 15], [512, 512, 5]]

        [1] https://en.wikipedia.org/wiki/Internet_Mix

        :param traffic: list of traffic elements; each traffic element contains
                        the injection parameter for each flow group.
        :param duration: (int) injection time in seconds.
        """
        for traffic_param in traffic.values():
            fg_id = str(traffic_param['id'])
            config_element = self._get_config_element_by_flow_group_name(fg_id)
            if not config_element:
                raise exceptions.IxNetworkFlowNotPresent(flow_group=fg_id)

            type = traffic_param.get('traffic_type', 'fixedDuration')
            rate = traffic_param['rate']
            rate_unit = (
                'framesPerSecond' if traffic_param['rate_unit'] ==
                tp_base.TrafficProfileConfig.RATE_FPS else 'percentLineRate')
            weighted_range_pairs = self._parse_framesize(
                traffic_param['outer_l2']['framesize'])
            srcmac = str(traffic_param['outer_l2'].get('srcmac', '00:00:00:00:00:01'))
            dstmac = str(traffic_param['outer_l2'].get('dstmac', '00:00:00:00:00:02'))

            if traffic_param['outer_l2']['QinQ']:
                s_vlan = traffic_param['outer_l2']['QinQ']['S-VLAN']
                c_vlan = traffic_param['outer_l2']['QinQ']['C-VLAN']

                field_descriptor = self._get_field_in_stack_item(
                    self._get_stack_item(fg_id, PROTO_ETHERNET)[0],
                    'etherType')

                self.ixnet.setMultiAttribute(field_descriptor,
                                             '-auto', 'false',
                                             '-singleValue', ETHER_TYPE_802_1ad,
                                             '-fieldValue', ETHER_TYPE_802_1ad,
                                             '-valueType', SINGLE_VALUE)

                self._append_procotol_to_stack(
                    PROTO_VLAN, config_element + '/stack:"ethernet-1"')
                self._append_procotol_to_stack(
                    PROTO_VLAN, config_element + '/stack:"ethernet-1"')

                self._update_vlan_tag(fg_id, s_vlan, S_VLAN)
                self._update_vlan_tag(fg_id, c_vlan, C_VLAN)

            self.ixnet.setMultiAttribute(
                config_element + '/transmissionControl',
                '-type', type, '-duration', duration)
            self.ixnet.setMultiAttribute(
                config_element + '/frameRate',
                '-rate', rate, '-type', rate_unit)
            self.ixnet.setMultiAttribute(
                config_element + '/frameSize',
                '-type', 'weightedPairs',
                '-weightedRangePairs', weighted_range_pairs)
            self.ixnet.commit()

            self._update_frame_mac(
                self._get_stack_item(fg_id, PROTO_ETHERNET)[0],
                'destinationAddress', dstmac)
            self._update_frame_mac(
                self._get_stack_item(fg_id, PROTO_ETHERNET)[0],
                'sourceAddress', srcmac)

    def _update_vlan_tag(self, fg_id, params, vlan=0):
        field_to_param_map = {
            'vlanUserPriority': 'priority',
            'cfi': 'cfi',
            'vlanID': 'id'
        }
        for field, param in field_to_param_map.items():
            value = params.get(param)
            if value:
                field_descriptor = self._get_field_in_stack_item(
                    self._get_stack_item(fg_id, PROTO_VLAN)[vlan],
                    field)

                self.ixnet.setMultiAttribute(field_descriptor,
                                             '-auto', 'false',
                                             '-singleValue', value,
                                             '-fieldValue', value,
                                             '-valueType', SINGLE_VALUE)

        self.ixnet.commit()

    def _update_ipv4_address(self, ip_descriptor, field, ip_address, seed,
                             mask, count):
        """Set the IPv4 address in a config element stack IP field

        :param ip_descriptor: (str) IP descriptor, e.g.:
            /traffic/trafficItem:1/configElement:1/stack:"ipv4-2"
        :param field: (str) field name, e.g.: scrIp, dstIp
        :param ip_address: (str) IP address
        :param seed: (int) seed length
        :param mask: (int) IP address mask length
        :param count: (int) number of random IPs to generate
        """
        field_descriptor = self._get_field_in_stack_item(ip_descriptor,
                                                         field)
        random_mask = str(ipaddress.IPv4Address(
            2**(ipaddress.IPV4LENGTH - mask) - 1).compressed)
        self.ixnet.setMultiAttribute(field_descriptor,
                                     '-seed', seed,
                                     '-fixedBits', ip_address,
                                     '-randomMask', random_mask,
                                     '-valueType', 'random',
                                     '-countValue', count)
        self.ixnet.commit()

    def update_ip_packet(self, traffic):
        """Update the IP packet

        NOTE: Only IPv4 is currently supported.
        :param traffic: list of traffic elements; each traffic element contains
                        the injection parameter for each flow group.
        """
        # NOTE(ralonsoh): L4 configuration is not set.
        for traffic_param in traffic.values():
            fg_id = str(traffic_param['id'])
            if not self._get_config_element_by_flow_group_name(fg_id):
                raise exceptions.IxNetworkFlowNotPresent(flow_group=fg_id)

            count = traffic_param['outer_l3']['count']
            srcip = str(traffic_param['outer_l3']['srcip'])
            dstip = str(traffic_param['outer_l3']['dstip'])
            srcseed = traffic_param['outer_l3']['srcseed']
            dstseed = traffic_param['outer_l3']['dstseed']
            srcmask = traffic_param['outer_l3']['srcmask'] or IP_VERSION_4_MASK
            dstmask = traffic_param['outer_l3']['dstmask'] or IP_VERSION_4_MASK

            self._update_ipv4_address(
                self._get_stack_item(fg_id, PROTO_IPV4)[0],
                'srcIp', srcip, srcseed, srcmask, count)
            self._update_ipv4_address(
                self._get_stack_item(fg_id, PROTO_IPV4)[0],
                'dstIp', dstip, dstseed, dstmask, count)

    def update_l4(self, traffic):
        """Update the L4 headers

        NOTE: Only UDP is currently supported
        :param traffic: list of traffic elements; each traffic element contains
                        the injection parameter for each flow group
        """
        for traffic_param in traffic.values():
            fg_id = str(traffic_param['id'])
            if not self._get_config_element_by_flow_group_name(fg_id):
                raise exceptions.IxNetworkFlowNotPresent(flow_group=fg_id)

            proto = traffic_param['outer_l3']['proto']
            if proto not in SUPPORTED_PROTO:
                raise exceptions.IXIAUnsupportedProtocol(protocol=proto)

            count = traffic_param['outer_l4']['count']
            seed = traffic_param['outer_l4']['seed']

            srcport = traffic_param['outer_l4']['srcport']
            srcmask = traffic_param['outer_l4']['srcportmask']

            dstport = traffic_param['outer_l4']['dstport']
            dstmask = traffic_param['outer_l4']['dstportmask']

            if proto in SUPPORTED_PROTO:
                self._update_udp_port(self._get_stack_item(fg_id, proto)[0],
                                      'srcPort', srcport, seed, srcmask, count)

                self._update_udp_port(self._get_stack_item(fg_id, proto)[0],
                                      'dstPort', dstport, seed, dstmask, count)

    def _update_udp_port(self, descriptor, field, value,
                         seed=1, mask=0, count=1):
        """Set the UDP port in a config element stack UDP field

        :param udp_descriptor: (str) UDP descriptor, e.g.:
            /traffic/trafficItem:1/configElement:1/stack:"udp-3"
        :param field: (str) field name, e.g.: scrPort, dstPort
        :param value: (int) UDP port fixed bits
        :param seed: (int) seed length
        :param mask: (int) UDP port mask
        :param count: (int) number of random ports to generate
        """
        field_descriptor = self._get_field_in_stack_item(descriptor, field)

        if mask == 0:
            seed = count = 1

        self.ixnet.setMultiAttribute(field_descriptor,
                                     '-auto', 'false',
                                     '-seed', seed,
                                     '-fixedBits', value,
                                     '-randomMask', mask,
                                     '-valueType', 'random',
                                     '-countValue', count)

        self.ixnet.commit()

    def _build_stats_map(self, view_obj, name_map):
        return {data_yardstick: self.ixnet.execute(
            'getColumnValues', view_obj, data_ixia)
            for data_yardstick, data_ixia in name_map.items()}

    def _set_egress_flow_tracking(self, encapsulation, offset):
        """
        Set egress flow tracking options
        :param encapsulation: encapsulation type
        :type encapsulation: str, e.g. 'Ethernet'
        :param offset: offset type
        :type offset: str, e.g. 'IPv4 TOS Precedence (3 bits)'
        """
        traffic_item = self.ixnet.getList(self.ixnet.getRoot() + '/traffic',
                                          'trafficItem')[0]
        # Enable Egress Tracking
        self.ixnet.setAttribute(traffic_item, '-egressEnabled', True)
        self.ixnet.commit()

        # Set encapsulation type
        enc_obj = self.ixnet.getList(traffic_item, 'egressTracking')[0]
        self.ixnet.setAttribute(enc_obj, '-encapsulation', encapsulation)

        # Set offset
        self.ixnet.setAttribute(enc_obj, '-offset', offset)
        self.ixnet.commit()

    def _set_flow_tracking(self, track_by):
        """
        Set flow tracking options
        :param track_by: list of tracking fields
        :type track_by: list, e.g. ['vlanVlanId0','ipv4Precedence0']
        """
        traffic_item = self.ixnet.getList(self.ixnet.getRoot() + '/traffic',
                                          'trafficItem')[0]
        self.ixnet.setAttribute(traffic_item + '/tracking', '-trackBy', track_by)
        self.ixnet.commit()

    def get_statistics(self):
        """Retrieve port and flow statistics

        "Port Statistics" parameters are stored in self.PORT_STATS_NAME_MAP.
        "Flow Statistics" parameters are stored in self.LATENCY_NAME_MAP.

        :return: dictionary with the statistics; the keys of this dictionary
                 are PORT_STATS_NAME_MAP and LATENCY_NAME_MAP keys.
        """
        port_statistics = '::ixNet::OBJ-/statistics/view:"Port Statistics"'
        flow_statistics = '::ixNet::OBJ-/statistics/view:"Flow Statistics"'
        stats = self._build_stats_map(port_statistics,
                                      self.PORT_STATS_NAME_MAP)
        stats.update(self._build_stats_map(flow_statistics,
                                          self.LATENCY_NAME_MAP))
        return stats

    def start_protocols(self):
        self.ixnet.execute('startAllProtocols')

    def stop_protocols(self):
        self.ixnet.execute('stopAllProtocols')

    def start_traffic(self):
        """Start the traffic injection in the traffic item

        By configuration, there is only one traffic item. This function returns
        when the traffic state is TRAFFIC_STATUS_STARTED.
        """
        traffic_items = self.ixnet.getList('/traffic', 'trafficItem')
        if self.is_traffic_running():
            self.ixnet.execute('stop', '/traffic')
            # pylint: disable=unnecessary-lambda
            utils.wait_until_true(lambda: self.is_traffic_stopped())

        self.ixnet.execute('generate', traffic_items)
        self.ixnet.execute('apply', '/traffic')
        self.ixnet.execute('start', '/traffic')
        # pylint: disable=unnecessary-lambda
        utils.wait_until_true(lambda: self.is_traffic_running())

    def add_topology(self, name, vports):
        log.debug("add_topology: name='%s' ports='%s'", name, vports)
        obj = self.ixnet.add(self.ixnet.getRoot(), 'topology')
        self.ixnet.setMultiAttribute(obj, '-name', name, '-vports', vports)
        self.ixnet.commit()
        return obj

    def add_device_group(self, topology, name, multiplier):
        log.debug("add_device_group: tpl='%s', name='%s', multiplier='%s'",
                  topology, name, multiplier)

        obj = self.ixnet.add(topology, 'deviceGroup')
        self.ixnet.setMultiAttribute(obj, '-name', name, '-multiplier',
                                     multiplier)
        self.ixnet.commit()
        return obj

    def add_ethernet(self, dev_group, name):
        log.debug(
            "add_ethernet: device_group='%s' name='%s'", dev_group, name)
        obj = self.ixnet.add(dev_group, 'ethernet')
        self.ixnet.setMultiAttribute(obj, '-name', name)
        self.ixnet.commit()
        return obj

    def _create_vlans(self, ethernet, count):
        self.ixnet.setMultiAttribute(ethernet, '-useVlans', 'true')
        self.ixnet.setMultiAttribute(ethernet, '-vlanCount', count)
        self.ixnet.commit()

    def _configure_vlans(self, ethernet, vlans):
        vlans_obj = self.ixnet.getList(ethernet, 'vlan')
        for i, vlan_obj in enumerate(vlans_obj):
            if vlans[i].vlan_id_step is not None:
                vlan_id_obj = self.ixnet.getAttribute(vlan_obj, '-vlanId')
                self.ixnet.setMultiAttribute(vlan_id_obj, '-clearOverlays',
                                             'true', '-pattern', 'counter')
                vlan_id_counter = self.ixnet.add(vlan_id_obj, 'counter')
                self.ixnet.setMultiAttribute(vlan_id_counter, '-start',
                                             vlans[i].vlan_id, '-step',
                                             vlans[i].vlan_id_step,
                                             '-direction',
                                             vlans[i].vlan_id_direction)
            else:
                vlan_id_obj = self.ixnet.getAttribute(vlan_obj, '-vlanId')
                self.ixnet.setMultiAttribute(vlan_id_obj + '/singleValue',
                                             '-value', vlans[i].vlan_id)

            if vlans[i].prio_step is not None:
                prio_obj = self.ixnet.getAttribute(vlan_obj, '-priority')
                self.ixnet.setMultiAttribute(prio_obj, '-clearOverlays', 'true',
                                             '-pattern', 'counter')
                prio_counter = self.ixnet.add(prio_obj, 'counter')
                self.ixnet.setMultiAttribute(prio_counter,
                                        '-start', vlans[i].prio,
                                        '-step', vlans[i].prio_step,
                                        '-direction', vlans[i].prio_direction)
            elif vlans[i].prio is not None:
                prio_obj = self.ixnet.getAttribute(vlan_obj, '-priority')
                self.ixnet.setMultiAttribute(prio_obj + '/singleValue',
                                             '-value', vlans[i].prio)

            if vlans[i].tp_id is not None:
                tp_id_obj = self.ixnet.getAttribute(vlan_obj, '-tpid')
                self.ixnet.setMultiAttribute(tp_id_obj + '/singleValue',
                                             '-value', vlans[i].tp_id)

        self.ixnet.commit()

    def add_vlans(self, ethernet, vlans):
        log.debug("add_vlans: ethernet='%s'", ethernet)

        if vlans is None or len(vlans) == 0:
            raise RuntimeError(
                "Invalid 'vlans' argument. Expected list of Vlan instances.")

        self._create_vlans(ethernet, len(vlans))
        self._configure_vlans(ethernet, vlans)

    def add_ipv4(self, ethernet, name='',
                 addr=None, addr_step=None, addr_direction='increment',
                 prefix=None, prefix_step=None, prefix_direction='increment',
                 gateway=None, gw_step=None, gw_direction='increment'):
        log.debug("add_ipv4: ethernet='%s' name='%s'", ethernet, name)
        obj = self.ixnet.add(ethernet, 'ipv4')
        if name != '':
            self.ixnet.setAttribute(obj, '-name', name)
            self.ixnet.commit()

        if addr_step is not None:
            # handle counter pattern
            _address = self.ixnet.getAttribute(obj, '-address')
            self.ixnet.setMultiAttribute(_address, '-clearOverlays', 'true',
                                         '-pattern', 'counter')

            address_counter = self.ixnet.add(_address, 'counter')
            self.ixnet.setMultiAttribute(address_counter,
                                         '-start', addr,
                                         '-step', addr_step,
                                         '-direction', addr_direction)
        elif addr is not None:
            # handle single value
            _address = self.ixnet.getAttribute(obj, '-address')
            self.ixnet.setMultiAttribute(_address + '/singleValue', '-value',
                                         addr)

        if prefix_step is not None:
            # handle counter pattern
            _prefix = self.ixnet.getAttribute(obj, '-prefix')
            self.ixnet.setMultiAttribute(_prefix, '-clearOverlays', 'true',
                                         '-pattern', 'counter')
            prefix_counter = self.ixnet.add(_prefix, 'counter')
            self.ixnet.setMultiAttribute(prefix_counter,
                                         '-start', prefix,
                                         '-step', prefix_step,
                                         '-direction', prefix_direction)
        elif prefix is not None:
            # handle single value
            _prefix = self.ixnet.getAttribute(obj, '-prefix')
            self.ixnet.setMultiAttribute(_prefix + '/singleValue', '-value',
                                         prefix)

        if gw_step is not None:
            # handle counter pattern
            _gateway = self.ixnet.getAttribute(obj, '-gatewayIp')
            self.ixnet.setMultiAttribute(_gateway, '-clearOverlays', 'true',
                                         '-pattern', 'counter')

            gateway_counter = self.ixnet.add(_gateway, 'counter')
            self.ixnet.setMultiAttribute(gateway_counter,
                                         '-start', gateway,
                                         '-step', gw_step,
                                         '-direction', gw_direction)
        elif gateway is not None:
            # handle single value
            _gateway = self.ixnet.getAttribute(obj, '-gatewayIp')
            self.ixnet.setMultiAttribute(_gateway + '/singleValue', '-value',
                                         gateway)

        self.ixnet.commit()
        return obj

    def add_pppox_client(self, xproto, auth, user, pwd):
        log.debug(
            "add_pppox_client: xproto='%s', auth='%s', user='%s', pwd='%s'",
            xproto, auth, user, pwd)
        obj = self.ixnet.add(xproto, 'pppoxclient')
        self.ixnet.commit()

        if auth == 'pap':
            auth_type = self.ixnet.getAttribute(obj, '-authType')
            self.ixnet.setMultiAttribute(auth_type + '/singleValue', '-value',
                                         auth)
            pap_user = self.ixnet.getAttribute(obj, '-papUser')
            self.ixnet.setMultiAttribute(pap_user + '/singleValue', '-value',
                                         user)
            pap_pwd = self.ixnet.getAttribute(obj, '-papPassword')
            self.ixnet.setMultiAttribute(pap_pwd + '/singleValue', '-value',
                                         pwd)
        else:
            raise NotImplementedError()

        self.ixnet.commit()
        return obj
