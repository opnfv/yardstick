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

            try:
                # values should be single-item dict, so just grab the first item
                try:
                    key, value = next(iter(values.items()))
                except StopIteration:
                    result[traffickey] = {}
                    continue

                port_id = value.get('id', 1)
                port_index = port_id - 1

                if value.get('outer_l3v4'):
                    ip = value['outer_l3v4']
                    src_key, dst_key = 'srcip4', 'dstip4'
                else:
                    ip = value['outer_l3v6']
                    src_key, dst_key = 'srcip6', 'dstip6'

                srcip, srcmask = self._get_ip_and_mask(ip[src_key])
                dstip, dstmask = self._get_ip_and_mask(ip[dst_key])

                outer_l4 = value.get('outer_l4')
                src_port, src_port_mask = self._get_fixed_and_mask(outer_l4['srcport'])
                dst_port, dst_port_mask = self._get_fixed_and_mask(outer_l4['dstport'])
                result[traffickey] = {
                    'bidir': False,
                    'id': port_id,
                    'rate': self.rate,
                    'rate_unit': self.rate_unit,
                    'outer_l2': {
                        'framesize': value['outer_l2']['framesize'],
                        'framesPerSecond': True,
                        'QinQ': value['outer_l2'].get('QinQ'),
                        'srcmac': mac['src_mac_{}'.format(port_index)],
                        'dstmac': mac['dst_mac_{}'.format(port_index)],
                    },
                    'outer_l3': {
                        'count': ip['count'],
                        'dscp': ip['dscp'],
                        'ttl': ip['ttl'],
                        'seed': ip['seed'],
                        'srcip': srcip,
                        'dstip': dstip,
                        'srcmask': srcmask,
                        'dstmask': dstmask,
                        'type': key,
                        'proto': ip['proto'],
                    },
                    'outer_l4': {
                        'srcport': src_port,
                        'dstport': dst_port,
                        'srcportmask': src_port_mask,
                        'dstportmask': dst_port_mask,
                        'count': outer_l4['count'],
                        'seed': outer_l4['seed'],
                    }

                }
            except KeyError:
                continue

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
            self.full_profile = {}
            self.pg_id = 0
            self.update_traffic_profile(traffic_generator)
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

        samples['TxThroughput'] = tx_throughput
        samples['RxThroughput'] = rx_throughput
        samples['DropPercentage'] = drop_percent

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

        samples['Status'] = self.STATUS_FAIL
        if round(drop_percent, precision) <= tolerance:
            samples['Status'] = self.STATUS_SUCCESS

        return completed, samples
