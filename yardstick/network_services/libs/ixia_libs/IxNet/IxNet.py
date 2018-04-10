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

import re
from itertools import product
import IxNetwork


log = logging.getLogger(__name__)

IP_VERSION_4 = 4
IP_VERSION_6 = 6
PROTO_IPV4 = 'ipv4'
PROTO_IPV6 = 'ipv6'
PROTO_UDP = 'udp'
PROTO_TCP = 'tcp'
PROTO_VLAN = 'vlan'


class TrafficStreamHelper(object):

    TEMPLATE = '{0.traffic_item}/{0.stream}:{0.param_id}/{1}'

    def __init__(self, traffic_item, stream, param_id):
        super(TrafficStreamHelper, self).__init__()
        self.traffic_item = traffic_item
        self.stream = stream
        self.param_id = param_id

    def __getattr__(self, item):
        return self.TEMPLATE.format(self, item)


class FramesizeHelper(object):

    def __init__(self):
        super(FramesizeHelper, self).__init__()
        self.weighted_pairs = []
        self.weighted_range_pairs = []

    @property
    def weighted_pairs_arg(self):
        return '-weightedPairs', self.weighted_pairs

    @property
    def weighted_range_pairs_arg(self):
        return '-weightedRangePairs', self.weighted_range_pairs

    def make_args(self, *args):
        return self.weighted_pairs_arg + self.weighted_range_pairs_arg + args

    def populate_data(self, framesize_data):
        for key, value in framesize_data.items():
            if value == '0':
                continue

            replaced = re.sub('[Bb]', '', key)
            self.weighted_pairs.extend([
                replaced,
                value,
            ])
            pairs = [
                replaced,
                replaced,
                value,
            ]
            self.weighted_range_pairs.append(pairs)


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

    def __init__(self, ixnet=None):
        self.ixnet = ixnet
        self._objRefs = dict()
        self._cfg = None
        self._params = None
        self._bidir = None

    def iter_over_get_lists(self, x1, x2, y2, offset=0):
        for x in self.ixnet.getList(x1, x2):
            y_list = self.ixnet.getList(x, y2)
            for i, y in enumerate(y_list, offset):
                yield x, y, i

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

    def connect(self, tg_cfg):
        self._cfg = self.get_config(tg_cfg)
        self.ixnet = IxNetwork.IxNet()

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

    def _create_traffic_item(self):
        """Create the traffic item to hold the flow groups

        The traffic item tracking by "Traffic Item" is enabled to retrieve the
        latency statistics.
        """
        log.info('Create the traffic item "RFC2455"')
        traffic_item = self.ixnet.add(self.ixnet.getRoot() + '/traffic',
                                      'trafficItem')
        self.ixnet.setMultiAttribute(traffic_item, '-name', 'RFC2455',
                                     '-trafficType', 'raw')
        self.ixnet.commit()

        traffic_item_id = self.ixnet.remapIds(traffic_item)[0]
        self.ixnet.setAttribute(traffic_item_id + '/tracking',
                                '-trackBy', 'trafficGroupId0')
        self.ixnet.commit()

    def _create_flow_groups(self):
        """Create the flow groups between the assigned ports"""
        traffic_item_id = self.ixnet.getList(self.ixnet.getRoot() + 'traffic',
                                             'trafficItem')[0]
        log.info('Create the flow groups')
        vports = self.ixnet.getList(self.ixnet.getRoot(), 'vport')
        uplink_ports = vports[::2]
        downlink_ports = vports[1::2]
        for up, down in zip(uplink_ports, downlink_ports):
            log.info('FGs: %s <--> %s', up, down)
            endpoint_set_1 = self.ixnet.add(traffic_item_id, 'endpointSet')
            endpoint_set_2 = self.ixnet.add(traffic_item_id, 'endpointSet')
            self.ixnet.setMultiAttribute(
                endpoint_set_1,
                '-sources', [up + ' /protocols'],
                '-destinations', [down + '/protocols'])
            self.ixnet.setMultiAttribute(
                endpoint_set_2,
                '-sources', [down + ' /protocols'],
                '-destinations', [up + '/protocols'])
            self.ixnet.commit()

    def _append_procotol_to_stack(self, protocol_name, previous_element):
        """Append a new element in the packet definition stack"""
        protocol = (self.ixnet.getRoot() +
                    '/traffic/protocolTemplate:"{}"'.format(protocol_name))
        self.ixnet.execute('append', previous_element, protocol)

    def _setup_config_elements(self):
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
            self._append_procotol_to_stack(
                PROTO_UDP, config_element + '/stack:"ethernet-1"')
            self._append_procotol_to_stack(
                PROTO_IPV4, config_element + '/stack:"ethernet-1"')

    def create_traffic_model(self):
        """Create a traffic item and the needed flow groups

        Each flow group inside the traffic item (only one is present)
        represents the traffic between two ports:
                        (uplink)    (downlink)
            FlowGroup1: port1    -> port2
            FlowGroup2: port1    <- port2
            FlowGroup3: port3    -> port4
            FlowGroup4: port3    <- port4
        """
        self._create_traffic_item()
        self._create_flow_groups()
        self._setup_config_elements()

    def ix_update_frame(self, params):
        streams = ["configElement"]

        for param in params.values():
            framesize_data = FramesizeHelper()
            traffic_items = self.ixnet.getList('/traffic', 'trafficItem')
            param_id = param['id']
            for traffic_item, stream in product(traffic_items, streams):
                helper = TrafficStreamHelper(traffic_item, stream, param_id)

                self.ixnet.setMultiAttribute(helper.transmissionControl,
                                             '-type', '{0}'.format(param.get('traffic_type',
                                                                             'fixedDuration')),
                                             '-duration', '{0}'.format(param.get('duration',
                                                                                 "30")))

                stream_frame_rate_path = helper.frameRate
                self.ixnet.setMultiAttribute(stream_frame_rate_path, '-rate', param['iload'])
                if param['outer_l2']['framesPerSecond']:
                    self.ixnet.setMultiAttribute(stream_frame_rate_path,
                                                 '-type', 'framesPerSecond')

                framesize_data.populate_data(param['outer_l2']['framesize'])

                make_attr_args = framesize_data.make_args('-incrementFrom', '66',
                                                          '-randomMin', '66',
                                                          '-quadGaussian', [],
                                                          '-type', 'weightedPairs',
                                                          '-presetDistribution', 'cisco',
                                                          '-incrementTo', '1518')

                self.ixnet.setMultiAttribute(helper.frameSize, *make_attr_args)

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

    def ix_update_udp(self, params):
        pass

    def ix_update_tcp(self, params):
        pass

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

    def build_stats_map(self, view_obj, name_map):
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
        stats = self.build_stats_map(port_statistics, self.PORT_STATS_NAME_MAP)
        stats.update(self.build_stats_map(flow_statistics,
                                          self.LATENCY_NAME_MAP))
        return stats
