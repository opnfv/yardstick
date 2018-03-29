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

    STATS_NAME_MAP = {
        "traffic_item": 'Traffic Item',
        "Tx_Frames": 'Tx Frames',
        "Rx_Frames": 'Rx Frames',
        "Tx_Frame_Rate": 'Tx Frame Rate',
        "Rx_Frame_Rate": 'Tx Frame Rate',
        "Store-Forward_Avg_latency_ns": 'Store-Forward Avg Latency (ns)',
        "Store-Forward_Min_latency_ns": 'Store-Forward Min Latency (ns)',
        "Store-Forward_Max_latency_ns": 'Store-Forward Max Latency (ns)',
    }

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
    def find_view_obj(view_name, views):
        edited_view_name = '::ixNet::OBJ-/statistics/view:"{}"'.format(view_name)
        return next((view for view in views if edited_view_name == view), '')

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

    def __init__(self, ixnet=None):
        self.ixnet = ixnet
        self._objRefs = dict()
        self._cfg = None
        self._logger = logging.getLogger(__name__)
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

    def _connect(self, tg_cfg):
        self._cfg = self.get_config(tg_cfg)
        self.ixnet = IxNetwork.IxNet()

        machine = self._cfg['machine']
        port = str(self._cfg['port'])
        version = str(self._cfg['version'])
        result = self.ixnet.connect(machine, '-port', port, '-version', version)
        return result

    def clear_ixia_config(self):
        self.ixnet.execute('newConfig')

    def load_ixia_profile(self, profile):
        self.ixnet.execute('loadConfig', self.ixnet.readFrom(profile))

    def ix_load_config(self, profile):
        self.clear_ixia_config()
        self.load_ixia_profile(profile)

    def ix_assign_ports(self):
        vports = self.ixnet.getList(self.ixnet.getRoot(), 'vport')
        ports = []

        chassis = self._cfg['chassis']
        ports = [(chassis, card, port) for card, port in
                 zip(self._cfg['cards'], self._cfg['ports'])]

        vport_list = self.ixnet.getList("/", "vport")
        self.ixnet.execute('assignPorts', ports, [], vport_list, True)
        self.ixnet.commit()

        for vport in vports:
            if self.ixnet.getAttribute(vport, '-state') != 'up':
                log.error("Both thr ports are down...")

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
                                                                             'continuous')),
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
        return {kl: self.execute_get_column_values(view_obj, kr) for kl, kr in name_map.items()}

    def execute_get_column_values(self, view_obj, name):
        return self.ixnet.execute('getColumnValues', view_obj, name)

    def ix_get_statistics(self):
        views = self.ixnet.getList('/statistics', 'view')
        stats = {}
        view_obj = self.find_view_obj("Traffic Item Statistics", views)
        stats = self.build_stats_map(view_obj, self.STATS_NAME_MAP)

        view_obj = self.find_view_obj("Port Statistics", views)
        ports_stats = self.build_stats_map(view_obj, self.PORT_STATS_NAME_MAP)

        view_obj = self.find_view_obj("Flow Statistics", views)
        stats["latency"] = self.build_stats_map(view_obj, self.LATENCY_NAME_MAP)

        return stats, ports_stats
