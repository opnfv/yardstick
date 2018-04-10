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

import logging

###from itertools import product
import IxNetwork
###import re

from yardstick.common import exceptions


log = logging.getLogger(__name__)

IP_VERSION_4 = 4
IP_VERSION_6 = 6


class IxNextgen(object):

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

    RANDOM_MASK_MAP = {
        IP_VERSION_4: '0.0.0.255',
        IP_VERSION_6: '0:0:0:0:0:0:0:ff',
    }

    MODE_SEEDS_MAP = {
        0: ('uplink', ['256', '2048']),
    }

    MODE_SEEDS_DEFAULT = 'downlink', ['2048', '256']

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
            'py_lib_path': tg_cfg["mgmt-interface"]["tg-config"]["py_lib_path"],
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

    def __init__(self):
        self._ixnet = None
        self._objRefs = dict()
        self._cfg = None
        self._params = None
        self._bidir = None

    @property
    def ixnet(self):
        if self._ixnet:
            return self._ixnet
        raise exceptions.IxNetworkClientNotConnected()

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

    @staticmethod
    def _parse_framesize(framesize):
        """Parse "framesize" config param. to return a list of weighted pairs

        :param framesize: dictionary of frame sizes and weights
        :return: list of paired frame sizes and weights
        """
        weighted_range_pairs = []
        for size, weight in framesize.items():
            weighted_range_pairs.append(int(size.upper().replace('B', '')))
            weighted_range_pairs.append(int(weight))
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
        for port in ports:
            vport = self.ixnet.add(self.ixnet.getRoot(), 'vport')
            self.ixnet.commit()
            self.ixnet.execute('assignPorts', [port], [], [vport], True)
            self.ixnet.commit()
            if self.ixnet.getAttribute(vport, '-state') != 'up':
                log.warning('Port %s is down', vport)

    def create_traffic_item(self):
        """Create a traffic item and the needed flow groups

        Each flow group inside the traffic item (only one is present)
        represents the traffic between two ports:
                        (uplink)    (downlink)
            FlowGroup1: port1    -> port2
            FlowGroup2: port1    <- port2
            FlowGroup3: port3    -> port4
            FlowGroup4: port3    <- port4

        The traffic item is configured to allow individual configurations per
        flow group. The traffic item tracking by "Traffic Item" is enabled to
        retrieve the latency statistics.
        """
        log.info('Create the traffic item "RFC2455"')
        traffic_item = self.ixnet.add(self.ixnet.getRoot() + '/traffic',
                                      'trafficItem')
        self.ixnet.setMultiAttribute(traffic_item, '-name', 'RFC2455',
                                     '-trafficType', 'raw')
        self.ixnet.commit()

        traffic_item_id = self.ixnet.remapIds(traffic_item)[0]

        log.info('Create the flow groups')
        vports = self.ixnet.getList(self.ixnet.getRoot(), 'vport')
        uplink_ports = vports[::2]
        downlink_ports = vports[1::2]
        index = 0
        for up, down in zip(uplink_ports, downlink_ports):
            log.info('FGs: %s <--> %s', up, down)
            endpoint_set_1 = self.ixnet.add(traffic_item_id, 'endpointSet')
            endpoint_set_2 = self.ixnet.add(traffic_item_id, 'endpointSet')
            self.ixnet.setMultiAttribute(
                endpoint_set_1, '-name', str(index + 1),
                '-sources', [up + ' /protocols'],
                '-destinations', [down + '/protocols'])
            self.ixnet.setMultiAttribute(
                endpoint_set_2, '-name', str(index + 2),
                '-sources', [down + ' /protocols'],
                '-destinations', [up + '/protocols'])
            self.ixnet.commit()
            index += 2

        log.info('Split the frame rate distribution per config element')
        config_elements = self.ixnet.getList(traffic_item_id, 'configElement')
        for config_element in config_elements:
            self.ixnet.setAttribute(config_element + '/frameRateDistribution',
                                    '-portDistribution', 'splitRateEvenly')
            self.ixnet.setAttribute(config_element + '/frameRateDistribution',
                                    '-streamDistribution', 'splitRateEvenly')
            self.ixnet.commit()

        log.info('Enable flow tracking to retrieve latency statistics')
        self.ixnet.setAttribute(traffic_item_id + '/tracking',
                                '-trackBy', 'trafficGroupId0')
        self.ixnet.commit()

    def update_frame(self, traffic):
        """Update the L2 frame

        This function updates the L2 frame options:
        - Traffic type: "continuous", "fixedDuration".
        - Duration: in case of traffic_type="fixedDuration", amount of seconds
                    to inject traffic.
        - Rate: in frames per seconds or percentage.
        - Type of rate: "framesPerSecond" ("bitsPerSecond" and
                        "percentLineRate" no used)
        - Frame size: custom IMIX [1] definition; a list of packet size in
                      bytes and the weight. E.g.:
                      [64, 10, 128, 15, 512, 5]

        [1] https://en.wikipedia.org/wiki/Internet_Mix

        :param traffic: list of traffic elements; each traffic element contains
                        the injection parameter for each flow group.
        """
        for traffic_item in traffic.values():
            config_element = self._get_config_element_by_flow_group_name(
                str(traffic_item['id']))
            if not config_element:
                raise exceptions.IxNetworkFlowNotPresent(
                    flow_group=traffic_item['id'])

            type = traffic_item.get('traffic_type', 'fixedDuration')
            duration = traffic_item.get('duration', 30)
            rate = traffic_item['iload']
            weighted_range_pairs = self._parse_framesize(
                traffic_item['outer_l2']['framesize'])

            self.ixnet.setMultiAttribute(
                config_element + '/transmissionControl',
                '-type', type, '-duration', duration)
            self.ixnet.setMultiAttribute(
                config_element + '/frameRate',
                '-rate', rate, '-type', 'framesPerSecond')
            self.ixnet.setMultiAttribute(
                config_element + '/frameSize',
                '-type', 'weightedPairs',
                '-weightedRangePairs', weighted_range_pairs)
            self.ixnet.commit()

    def update_ether_multi_attribute(self, ether, mac_addr):
        self.ixnet.setMultiAttribute(ether,
                                     '-singleValue', mac_addr,
                                     '-fieldValue', mac_addr,
                                     '-valueType', 'singleValue')

    def update_ether_multi_attributes(self, ether, l2):
        if "ethernet.header.destinationAddress" in ether:
            self.update_ether_multi_attribute(ether, str(l2.get('dstmac', "00:00:00:00:00:02")))

        if "ethernet.header.sourceAddress" in ether:
            self.update_ether_multi_attribute(ether, str(l2.get('srcmac', "00:00:00:00:00:01")))

    def ix_update_ether(self, params):
        for ti, ep, index in self.iter_over_get_lists('/traffic', 'trafficItem',
                                                      "configElement", 1):
            iter1 = (v['outer_l2'] for v in params.values() if str(v['id']) == str(index))
            try:
                l2 = next(iter1, {})
            except KeyError:
                continue

            for ip, ether, _ in self.iter_over_get_lists(ep, 'stack', 'field'):
                self.update_ether_multi_attributes(ether, l2)

        self.ixnet.commit()

    #########################################################################

    def set_random_ip_multi_attribute(self, ipv4, seed, fixed_bits, random_mask, l3_count):
        self.ixnet.setMultiAttribute(
            ipv4,
            '-seed', str(seed),
            '-fixedBits', str(fixed_bits),
            '-randomMask', str(random_mask),
            '-valueType', 'random',
            '-countValue', str(l3_count))


    def set_random_ip_multi_attributes(self, ip, version, seeds, l3):
        try:
            random_mask = self.RANDOM_MASK_MAP[version]
        except KeyError:
            raise ValueError('Unknown version %s' % version)

        l3_count = l3['count']
        if "srcIp" in ip:
            fixed_bits = l3['srcip4']
            self.set_random_ip_multi_attribute(ip, seeds[0], fixed_bits, random_mask, l3_count)
        if "dstIp" in ip:
            fixed_bits = l3['dstip4']
            self.set_random_ip_multi_attribute(ip, seeds[1], fixed_bits, random_mask, l3_count)

    def add_ip_header(self, params, version):
        for it, ep, i in self.iter_over_get_lists('/traffic', 'trafficItem', "configElement", 1):
            iter1 = (v['outer_l3'] for v in params.values() if str(v['id']) == str(i))
            try:
                l3 = next(iter1, {})
                seeds = self.MODE_SEEDS_MAP.get(i, self.MODE_SEEDS_DEFAULT)[1]
            except (KeyError, IndexError):
                continue

            for ip, ip_bits, _ in self.iter_over_get_lists(ep, 'stack', 'field'):
                self.set_random_ip_multi_attributes(ip_bits, version, seeds, l3)

        self.ixnet.commit()



    #########################################################################



    def ix_start_traffic(self):
        tis = self.ixnet.getList('/traffic', 'trafficItem')
        for ti in tis:
            self.ixnet.execute('generate', [ti])
            self.ixnet.execute('apply', '/traffic')
            self.ixnet.execute('start', '/traffic')

    def ix_stop_traffic(self):
        tis = self.ixnet.getList('/traffic', 'trafficItem')
        for _ in tis:
            self.ixnet.execute('stop', '/traffic')

    def _build_stats_map(self, view_obj, name_map):
        return {data_yardstick: self.ixnet.execute(
                'getColumnValues', view_obj, data_ixia)
            for data_yardstick, data_ixia in name_map.items()}

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
