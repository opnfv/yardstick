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
from collections import OrderedDict

from yardstick.common import utils
from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.traffic_profile import trex_traffic_profile


LOG = logging.getLogger(__name__)


class IXIARFC2544Profile(trex_traffic_profile.TrexProfile):

    UPLINK = 'uplink'
    DOWNLINK = 'downlink'
    DROP_PERCENT_ROUND = 6
    RATE_ROUND = 5
    STATUS_SUCCESS = "Success"
    STATUS_FAIL = "Failure"

    def __init__(self, yaml_data):
        super(IXIARFC2544Profile, self).__init__(yaml_data)
        self.rate = self.config.frame_rate
        self.rate_unit = self.config.rate_unit
        self.full_profile = {}

    def _get_ip_and_mask(self, ip_range):
        _ip_range = ip_range.split('-')
        if len(_ip_range) == 1:
            return _ip_range[0], None

        mask = utils.get_mask_from_ip_range(_ip_range[0], _ip_range[1])
        return _ip_range[0], mask

    def _get_fixed_and_mask(self, port_range):
        _port_range = str(port_range).split('-')
        if len(_port_range) == 1:
            return int(_port_range[0]), 0

        return int(_port_range[0]), int(_port_range[1])

    def _get_ixia_traffic_profile(self, profile_data, mac=None):
        mac = {} if mac is None else mac
        result = {}
        for traffickey, values in profile_data.items():
            if not traffickey.startswith((self.UPLINK, self.DOWNLINK)):
                continue

            # values should be single-item dict, so just grab the first item
            try:
                key, value = next(iter(values.items()))
            except StopIteration:
                result[traffickey] = {}
                continue

            port_id = value.get('id', 1)
            port_index = port_id - 1

            result[traffickey] = {
                'bidir': False,
                'id': port_id,
                'rate': self.rate,
                'rate_unit': self.rate_unit,
                'outer_l2': {},
                'outer_l3': {},
                'outer_l4': {},
            }

            outer_l2 = value.get('outer_l2')
            if outer_l2:
                result[traffickey]['outer_l2'].update({
                    'framesize': outer_l2.get('framesize'),
                    'framesPerSecond': True,
                    'QinQ': outer_l2.get('QinQ'),
                    'srcmac': mac.get('src_mac_{}'.format(port_index)),
                    'dstmac': mac.get('dst_mac_{}'.format(port_index)),
                })

            if value.get('outer_l3v4'):
                outer_l3 = value['outer_l3v4']
                src_key, dst_key = 'srcip4', 'dstip4'
            else:
                outer_l3 = value.get('outer_l3v6')
                src_key, dst_key = 'srcip6', 'dstip6'
            if outer_l3:
                srcip = srcmask = dstip = dstmask = None
                if outer_l3.get(src_key):
                    srcip, srcmask = self._get_ip_and_mask(outer_l3[src_key])
                if outer_l3.get(dst_key):
                    dstip, dstmask = self._get_ip_and_mask(outer_l3[dst_key])

                result[traffickey]['outer_l3'].update({
                    'count': outer_l3.get('count', 1),
                    'dscp': outer_l3.get('dscp'),
                    'ttl': outer_l3.get('ttl'),
                    'srcseed': outer_l3.get('srcseed', 1),
                    'dstseed': outer_l3.get('dstseed', 1),
                    'srcip': srcip,
                    'dstip': dstip,
                    'srcmask': srcmask,
                    'dstmask': dstmask,
                    'type': key,
                    'proto': outer_l3.get('proto'),
                    'priority': outer_l3.get('priority')
                })

            outer_l4 = value.get('outer_l4')
            if outer_l4:
                src_port = src_port_mask = dst_port = dst_port_mask = None
                if outer_l4.get('srcport'):
                    src_port, src_port_mask = (
                        self._get_fixed_and_mask(outer_l4['srcport']))

                if outer_l4.get('dstport'):
                    dst_port, dst_port_mask = (
                        self._get_fixed_and_mask(outer_l4['dstport']))

                result[traffickey]['outer_l4'].update({
                    'srcport': src_port,
                    'dstport': dst_port,
                    'srcportmask': src_port_mask,
                    'dstportmask': dst_port_mask,
                    'count': outer_l4.get('count', 1),
                    'seed': outer_l4.get('seed', 1),
                })

        return result

    def _ixia_traffic_generate(self, traffic, ixia_obj):
        ixia_obj.update_frame(traffic, self.config.duration)
        ixia_obj.update_ip_packet(traffic)
        ixia_obj.update_l4(traffic)
        ixia_obj.start_traffic()

    def update_traffic_profile(self, traffic_generator):
        def port_generator():
            for vld_id, intfs in sorted(traffic_generator.networks.items()):
                if not vld_id.startswith((self.UPLINK, self.DOWNLINK)):
                    continue
                profile_data = self.params.get(vld_id)
                if not profile_data:
                    continue
                self.profile_data = profile_data
                self.full_profile.update({vld_id: self.profile_data})
                for intf in intfs:
                    yield traffic_generator.vnfd_helper.port_num(intf)

        self.ports = [port for port in port_generator()]

    def execute_traffic(self, traffic_generator, ixia_obj=None, mac=None):
        mac = {} if mac is None else mac
        first_run = self.first_run
        if self.first_run:
            self.first_run = False
            self.pg_id = 0
            self.max_rate = self.rate
            self.min_rate = 0.0
        else:
            self.rate = round(float(self.max_rate + self.min_rate) / 2.0,
                              self.RATE_ROUND)

        traffic = self._get_ixia_traffic_profile(self.full_profile, mac)
        self._ixia_traffic_generate(traffic, ixia_obj)
        return first_run

    def get_drop_percentage(self, samples, tol_min, tolerance, precision,
                            first_run=False):
        completed = False
        drop_percent = 100
        num_ifaces = len(samples)
        duration = self.config.duration
        in_packets_sum = sum(
            [samples[iface]['in_packets'] for iface in samples])
        out_packets_sum = sum(
            [samples[iface]['out_packets'] for iface in samples])
        rx_throughput = round(float(in_packets_sum) / duration, 3)
        tx_throughput = round(float(out_packets_sum) / duration, 3)
        packet_drop = abs(out_packets_sum - in_packets_sum)

        try:
            drop_percent = round(
                (packet_drop / float(out_packets_sum)) * 100,
                self.DROP_PERCENT_ROUND)
        except ZeroDivisionError:
            LOG.info('No traffic is flowing')

        if first_run:
            completed = True if drop_percent <= tolerance else False
        if (first_run and
                self.rate_unit == tp_base.TrafficProfileConfig.RATE_FPS):
            self.rate = float(out_packets_sum) / duration / num_ifaces

        if drop_percent > tolerance:
            self.max_rate = self.rate
        elif drop_percent < tol_min:
            self.min_rate = self.rate
        else:
            completed = True

        LOG.debug("tolerance=%s, tolerance_precision=%s drop_percent=%s "
                  "completed=%s", tolerance, precision, drop_percent,
                  completed)

        latency_ns_avg = float(
            sum([samples[iface]['Store-Forward_Avg_latency_ns']
            for iface in samples])) / num_ifaces
        latency_ns_min = float(
            sum([samples[iface]['Store-Forward_Min_latency_ns']
            for iface in samples])) / num_ifaces
        latency_ns_max = float(
            sum([samples[iface]['Store-Forward_Max_latency_ns']
            for iface in samples])) / num_ifaces

        samples['Status'] = self.STATUS_FAIL
        if round(drop_percent, precision) <= tolerance:
            samples['Status'] = self.STATUS_SUCCESS

        samples['TxThroughput'] = tx_throughput
        samples['RxThroughput'] = rx_throughput
        samples['DropPercentage'] = drop_percent
        samples['latency_ns_avg'] = latency_ns_avg
        samples['latency_ns_min'] = latency_ns_min
        samples['latency_ns_max'] = latency_ns_max

        return completed, samples


class IXIARFC2544PppoeScenarioProfile(IXIARFC2544Profile):
    def __init__(self, yaml_data):
        super(IXIARFC2544PppoeScenarioProfile, self).__init__(yaml_data)
        self.full_profile = OrderedDict()

    def _get_flow_groups_params(self):
        flows_data = [key for key in self.params.keys()
                      if key.split('_')[0] in [self.UPLINK, self.DOWNLINK]]
        for i in range(len(flows_data)):
            uplink = '_'.join([self.UPLINK, str(i)])
            downlink = '_'.join([self.DOWNLINK, str(i)])
            if uplink in flows_data:
                self.full_profile.update({uplink: self.params[uplink]})
            if downlink in flows_data:
                self.full_profile.update({downlink: self.params[downlink]})

    def update_traffic_profile(self, traffic_generator):

        networks = OrderedDict()

        # Sort network interfaces pairs
        for i in range(len(traffic_generator.networks)):
            uplink = '_'.join([self.UPLINK, str(i)])
            downlink = '_'.join([self.DOWNLINK, str(i)])
            if uplink in traffic_generator.networks:
                networks[uplink] = traffic_generator.networks[uplink]
            if downlink in traffic_generator.networks:
                networks[downlink] = traffic_generator.networks[downlink]

        def port_generator():
            for intfs in networks.values():
                for intf in intfs:
                    yield traffic_generator.vnfd_helper.port_num(intf)

        self._get_flow_groups_params()
        self.ports = [port for port in port_generator()]

    def _update_flows_drop_percentage(self, samples):
        port_drop_percent = 100
        for port_name in samples:
            port_stats = samples[port_name]
            for vlan_name in port_stats['vlan']:
                vlan_stats = port_stats['vlan'][vlan_name]
                for prio in vlan_stats['priority']:
                    prio_stats = vlan_stats['priority'][prio]
                    tx_frames = prio_stats['Tx_Frames']
                    frames_delta = prio_stats['Frames_Delta']
                    drop_rate = (float(frames_delta) * 100) / float(
                        tx_frames)
                    prio_stats['DropPercentage'] = round(drop_rate, 3)
                _vlan_drop_rate = (float(
                    vlan_stats['Frames_Delta']) * 100) / float(vlan_stats['Tx_Frames'])
                vlan_stats['DropPercentage'] = round(_vlan_drop_rate, 3)
            in_packets = port_stats['in_packets']
            out_packets = port_stats['out_packets']
            packet_drop = abs(out_packets - in_packets)
            try:
                port_drop_percent = round(
                    (packet_drop / float(out_packets)) * 100,
                    self.DROP_PERCENT_ROUND)
            except ZeroDivisionError:
                LOG.info('No traffic is flowing')
            port_stats['DropPercentage'] = port_drop_percent
        return samples

    def _get_summary_priority_flows_drop_percentage(self, samples):
        result = {}
        for iface in samples:
            for prio_id in samples[iface]['priority']:
                prio_data = samples[iface]['priority'][prio_id]
                if prio_id not in result:
                    result[prio_id] = {
                        'Tx_Frames': int(prio_data['Tx_Frames']),
                        'Rx_Frames': int(prio_data['Rx_Frames']),
                        'Frames_Delta': int(prio_data['Frames_Delta'])
                    }
                else:
                    result[prio_id]['Tx_Frames'] += int(prio_data['Tx_Frames'])
                    result[prio_id]['Rx_Frames'] += int(prio_data['Rx_Frames'])
                    result[prio_id]['Frames_Delta'] += int(prio_data['Frames_Delta'])

        for prio_id in result:
            tx_frames = result[prio_id]['Tx_Frames']
            frames_delta = result[prio_id]['Frames_Delta']
            drop_percentage = (float(frames_delta) * 100) / float(tx_frames)
            result[prio_id]['DropPercentage'] = round(drop_percentage, 3)
        return result

    def get_drop_percentage(self, samples, tol_min, tolerance, precision,
                            first_run=False):
        samples = self._update_flows_drop_percentage(samples)
        summary_prio_flows_stats = \
            self._get_summary_priority_flows_drop_percentage(samples)
        completed = False
        drop_percent = 100
        num_ifaces = len(samples)
        duration = self.config.duration
        in_packets_sum = sum(
            [samples[iface]['in_packets'] for iface in samples])
        out_packets_sum = sum(
            [samples[iface]['out_packets'] for iface in samples])
        rx_throughput = round(float(in_packets_sum) / duration, 3)
        tx_throughput = round(float(out_packets_sum) / duration, 3)
        packet_drop = abs(out_packets_sum - in_packets_sum)

        try:
            drop_percent = round(
                (packet_drop / float(out_packets_sum)) * 100,
                self.DROP_PERCENT_ROUND)
        except ZeroDivisionError:
            LOG.info('No traffic is flowing')

        if first_run:
            completed = True if drop_percent <= tolerance else False
        if (first_run and
                self.rate_unit == tp_base.TrafficProfileConfig.RATE_FPS):
            self.rate = float(out_packets_sum) / duration / num_ifaces

        if drop_percent > tolerance:
            self.max_rate = self.rate
        elif drop_percent < tol_min:
            self.min_rate = self.rate
        else:
            completed = True

        LOG.debug("tolerance=%s, tolerance_precision=%s drop_percent=%s "
                  "completed=%s", tolerance, precision, drop_percent,
                  completed)

        latency_ns_avg = float(
            sum([samples[iface]['Store-Forward_Avg_latency_ns']
            for iface in samples])) / num_ifaces
        latency_ns_min = float(
            sum([samples[iface]['Store-Forward_Min_latency_ns']
            for iface in samples])) / num_ifaces
        latency_ns_max = float(
            sum([samples[iface]['Store-Forward_Max_latency_ns']
            for iface in samples])) / num_ifaces

        samples['Status'] = self.STATUS_FAIL
        if round(drop_percent, precision) <= tolerance:
            samples['Status'] = self.STATUS_SUCCESS

        samples['TxThroughput'] = tx_throughput
        samples['RxThroughput'] = rx_throughput
        samples['DropPercentage'] = drop_percent
        samples['latency_ns_avg'] = latency_ns_avg
        samples['latency_ns_min'] = latency_ns_min
        samples['latency_ns_max'] = latency_ns_max
        samples['priority'] = summary_prio_flows_stats

        return completed, samples
