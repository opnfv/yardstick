# Copyright (c) 2016-2019 Intel Corporation
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
import collections

from yardstick.common import utils
from yardstick.network_services.traffic_profile import base as tp_base
from yardstick.network_services.traffic_profile import trex_traffic_profile


LOG = logging.getLogger(__name__)


class IXIARFC2544Profile(trex_traffic_profile.TrexProfile):

    UPLINK = 'uplink'
    DOWNLINK = 'downlink'
    DROP_PERCENT_ROUND = 6
    STATUS_SUCCESS = "Success"
    STATUS_FAIL = "Failure"

    def __init__(self, yaml_data):
        super(IXIARFC2544Profile, self).__init__(yaml_data)
        self.rate = self.config.frame_rate
        self.rate_unit = self.config.rate_unit
        self.iteration = 0
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

            frame_rate = value.get('frame_rate')
            if frame_rate:
                flow_rate, flow_rate_unit = self.config.parse_rate(frame_rate)
                result[traffickey]['rate'] = flow_rate
                result[traffickey]['rate_unit'] = flow_rate_unit

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

    def _ixia_traffic_generate(self, traffic, ixia_obj, traffic_gen):
        ixia_obj.update_frame(traffic, self.config.duration)
        ixia_obj.update_ip_packet(traffic)
        ixia_obj.update_l4(traffic)
        self._update_traffic_tracking_options(traffic_gen)
        ixia_obj.start_traffic()

    def _update_traffic_tracking_options(self, traffic_gen):
        traffic_gen.update_tracking_options()

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
            self.rate = self._get_next_rate()

        self.iteration = traffic_generator.rfc_helper.iteration.value
        traffic = self._get_ixia_traffic_profile(self.full_profile, mac)
        self._ixia_traffic_generate(traffic, ixia_obj, traffic_generator)
        return first_run

    # pylint: disable=unused-argument
    def get_drop_percentage(self, samples, tol_min, tolerance, precision,
                            resolution, first_run=False, tc_rfc2544_opts=None):
        completed = False
        drop_percent = 100.0
        num_ifaces = len(samples)
        duration = self.config.duration
        in_packets_sum = sum(
            [samples[iface]['InPackets'] for iface in samples])
        out_packets_sum = sum(
            [samples[iface]['OutPackets'] for iface in samples])
        in_bytes_sum = sum(
            [samples[iface]['InBytes'] for iface in samples])
        out_bytes_sum = sum(
            [samples[iface]['OutBytes'] for iface in samples])
        rx_throughput = round(float(in_packets_sum) / duration, 3)
        tx_throughput = round(float(out_packets_sum) / duration, 3)
        # Rx throughput in Bps
        rx_throughput_bps = round(float(in_bytes_sum) / duration, 3)
        # Tx throughput in Bps
        tx_throughput_bps = round(float(out_bytes_sum) / duration, 3)
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

        last_rate = self.rate
        next_rate = self._get_next_rate()
        if abs(next_rate - self.rate) < resolution:
            LOG.debug("rate=%s, next_rate=%s, resolution=%s", self.rate,
                      next_rate, resolution)
            # stop test if the difference between the rate transmission
            # in two iterations is smaller than the value of the resolution
            completed = True

        LOG.debug("tolerance=%s, tolerance_precision=%s drop_percent=%s "
                  "completed=%s", tolerance, precision, drop_percent,
                  completed)

        latency_ns_avg = float(sum(
            [samples[iface]['LatencyAvg'] for iface in samples])) / num_ifaces
        latency_ns_min = min([samples[iface]['LatencyMin'] for iface in samples])
        latency_ns_max = max([samples[iface]['LatencyMax'] for iface in samples])

        samples['Status'] = self.STATUS_FAIL
        if round(drop_percent, precision) <= tolerance:
            samples['Status'] = self.STATUS_SUCCESS

        samples['TxThroughput'] = tx_throughput
        samples['RxThroughput'] = rx_throughput
        samples['TxThroughputBps'] = tx_throughput_bps
        samples['RxThroughputBps'] = rx_throughput_bps
        samples['DropPercentage'] = drop_percent
        samples['LatencyAvg'] = latency_ns_avg
        samples['LatencyMin'] = latency_ns_min
        samples['LatencyMax'] = latency_ns_max
        samples['Rate'] = last_rate
        samples['PktSize'] = self._get_framesize()
        samples['Iteration'] = self.iteration

        return completed, samples


class IXIARFC2544PppoeScenarioProfile(IXIARFC2544Profile):
    """Class handles BNG PPPoE scenario tests traffic profile"""

    def __init__(self, yaml_data):
        super(IXIARFC2544PppoeScenarioProfile, self).__init__(yaml_data)
        self.full_profile = collections.OrderedDict()

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

        networks = collections.OrderedDict()

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

    def _get_prio_flows_drop_percentage(self, stats):
        drop_percent = 100
        for prio_id in stats:
            prio_flow = stats[prio_id]
            sum_packet_drop = abs(prio_flow['OutPackets'] - prio_flow['InPackets'])
            try:
                drop_percent = round(
                    (sum_packet_drop / float(prio_flow['OutPackets'])) * 100,
                    self.DROP_PERCENT_ROUND)
            except ZeroDivisionError:
                LOG.info('No traffic is flowing')
            prio_flow['DropPercentage'] = drop_percent
        return stats

    def _get_summary_pppoe_subs_counters(self, samples):
        result = {}
        keys = ['SessionsUp',
                'SessionsDown',
                'SessionsNotStarted',
                'SessionsTotal']
        for key in keys:
            result[key] = \
                sum([samples[port][key] for port in samples
                     if key in samples[port]])
        return result

    def get_drop_percentage(self, samples, tol_min, tolerance, precision,
                            resolution, first_run=False, tc_rfc2544_opts=None):
        completed = False
        sum_drop_percent = 100
        num_ifaces = len(samples)
        duration = self.config.duration
        last_rate = self.rate
        priority_stats = samples.pop('priority_stats')
        priority_stats = self._get_prio_flows_drop_percentage(priority_stats)
        summary_subs_stats = self._get_summary_pppoe_subs_counters(samples)
        in_packets_sum = sum(
            [samples[iface]['InPackets'] for iface in samples])
        out_packets_sum = sum(
            [samples[iface]['OutPackets'] for iface in samples])
        in_bytes_sum = sum(
            [samples[iface]['InBytes'] for iface in samples])
        out_bytes_sum = sum(
            [samples[iface]['OutBytes'] for iface in samples])
        rx_throughput = round(float(in_packets_sum) / duration, 3)
        tx_throughput = round(float(out_packets_sum) / duration, 3)
        # Rx throughput in Bps
        rx_throughput_bps = round(float(in_bytes_sum) / duration, 3)
        # Tx throughput in Bps
        tx_throughput_bps = round(float(out_bytes_sum) / duration, 3)
        sum_packet_drop = abs(out_packets_sum - in_packets_sum)

        try:
            sum_drop_percent = round(
                (sum_packet_drop / float(out_packets_sum)) * 100,
                self.DROP_PERCENT_ROUND)
        except ZeroDivisionError:
            LOG.info('No traffic is flowing')

        latency_ns_avg = float(sum(
            [samples[iface]['LatencyAvg'] for iface in samples])) / num_ifaces
        latency_ns_min = min([samples[iface]['LatencyMin'] for iface in samples])
        latency_ns_max = max([samples[iface]['LatencyMax'] for iface in samples])

        samples['TxThroughput'] = tx_throughput
        samples['RxThroughput'] = rx_throughput
        samples['TxThroughputBps'] = tx_throughput_bps
        samples['RxThroughputBps'] = rx_throughput_bps
        samples['DropPercentage'] = sum_drop_percent
        samples['LatencyAvg'] = latency_ns_avg
        samples['LatencyMin'] = latency_ns_min
        samples['LatencyMax'] = latency_ns_max
        samples['Priority'] = priority_stats
        samples['Rate'] = last_rate
        samples['PktSize'] = self._get_framesize()
        samples['Iteration'] = self.iteration
        samples.update(summary_subs_stats)

        if tc_rfc2544_opts:
            priority = tc_rfc2544_opts.get('priority')
            if priority:
                drop_percent = samples['Priority'][priority]['DropPercentage']
            else:
                drop_percent = sum_drop_percent
        else:
            drop_percent = sum_drop_percent

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

        next_rate = self._get_next_rate()
        if abs(next_rate - self.rate) < resolution:
            LOG.debug("rate=%s, next_rate=%s, resolution=%s", self.rate,
                      next_rate, resolution)
            # stop test if the difference between the rate transmission
            # in two iterations is smaller than the value of the resolution
            completed = True

        LOG.debug("tolerance=%s, tolerance_precision=%s drop_percent=%s "
                  "completed=%s", tolerance, precision, drop_percent,
                  completed)

        samples['Status'] = self.STATUS_FAIL
        if round(drop_percent, precision) <= tolerance:
            samples['Status'] = self.STATUS_SUCCESS

        return completed, samples
