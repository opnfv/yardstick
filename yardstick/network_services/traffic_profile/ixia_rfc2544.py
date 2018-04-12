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

from yardstick.network_services.libs.ixia_libs.IxNet import IxNet
from yardstick.network_services.traffic_profile.trex_traffic_profile import \
    TrexProfile

LOG = logging.getLogger(__name__)


class IXIARFC2544Profile(TrexProfile):

    UPLINK = 'uplink'
    DOWNLINK = 'downlink'

    def _get_ixia_traffic_profile(self, profile_data, mac=None):
        if mac is None:
            mac = {}

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
                try:
                    ip = value['outer_l3v6']
                except KeyError:
                    ip = value['outer_l3v4']
                    src_key, dst_key = 'srcip4', 'dstip4'
                else:
                    src_key, dst_key = 'srcip6', 'dstip6'

                result[traffickey] = {
                    'bidir': False,
                    'iload': '100',
                    'id': port_id,
                    'outer_l2': {
                        'framesize': value['outer_l2']['framesize'],
                        'framesPerSecond': True,
                        'srcmac': mac['src_mac_{}'.format(port_index)],
                        'dstmac': mac['dst_mac_{}'.format(port_index)],
                    },
                    'outer_l3': {
                        'count': ip['count'],
                        'dscp': ip['dscp'],
                        'ttl': ip['ttl'],
                        src_key: ip[src_key].split("-")[0],
                        dst_key: ip[dst_key].split("-")[0],
                        'type': key,
                        'proto': ip['proto'],
                    },
                    'outer_l4': value['outer_l4'],
                }
            except KeyError:
                continue

        return result

    def _ixia_traffic_generate(self, traffic, ixia_obj):
        for key, value in traffic.items():
            if key.startswith((self.UPLINK, self.DOWNLINK)):
                value["iload"] = str(self.rate)
        ixia_obj.update_frame(traffic)
        ixia_obj.update_ip_packet(traffic)
        ixia_obj.start_traffic()
        self.tmp_drop = 0
        self.tmp_throughput = 0

    def update_traffic_profile(self, traffic_generator):
        def port_generator():
            for vld_id, intfs in sorted(traffic_generator.networks.items()):
                if not vld_id.startswith((self.UPLINK, self.DOWNLINK)):
                    continue
                profile_data = self.params.get(vld_id)
                if not profile_data:
                    continue
                self.profile_data = profile_data
                self.get_streams(self.profile_data)
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
            self.min_rate = 0

        self.rate = round((self.max_rate + self.min_rate) / 2.0, 2)
        traffic = self._get_ixia_traffic_profile(self.full_profile, mac)
        self._ixia_traffic_generate(traffic, ixia_obj)
        return first_run

    def get_drop_percentage(self, samples, tol_min, tolerance, duration=30.0,
                            first_run=False):
        completed = False
        drop_percent = 100
        num_ifaces = len(samples)
        in_packets_sum = sum([samples[iface]['in_packets']
                                for iface in samples])
        out_packets_sum = sum([samples[iface]['out_packets']
                                 for iface in samples])
        rx_throughput = sum([samples[iface]['RxThroughput']
                             for iface in samples])
        tx_throughput = sum([samples[iface]['TxThroughput']
                             for iface in samples])
        packet_drop = abs(out_packets_sum - in_packets_sum)
        try:
            drop_percent = round(
                (packet_drop / float(out_packets_sum)) * 100, 2)
        except ZeroDivisionError:
            LOG.info('No traffic is flowing')
        samples['TxThroughput'] = round(tx_throughput / 1.0, 2)
        samples['RxThroughput'] = round(rx_throughput / 1.0, 2)
        samples['CurrentDropPercentage'] = drop_percent
        samples['Throughput'] = self.tmp_throughput
        samples['DropPercentage'] = self.tmp_drop

        if drop_percent > tolerance and self.tmp_throughput == 0:
            samples['Throughput'] = round(rx_throughput / 1.0, 2)
            samples['DropPercentage'] = drop_percent

        if first_run:
            self.rate = out_packets_sum / duration / num_ifaces
            completed = True if drop_percent <= tolerance else False

        if drop_percent > tolerance:
            self.max_rate = self.rate
        elif drop_percent < tol_min:
            self.min_rate = self.rate
            if drop_percent >= self.tmp_drop:
                self.tmp_drop = drop_percent
                self.tmp_throughput = round((rx_throughput / 1.0), 2)
                samples['Throughput'] = round(rx_throughput / 1.0, 2)
                samples['DropPercentage'] = drop_percent
        else:
            samples['Throughput'] = round(rx_throughput / 1.0, 2)
            samples['DropPercentage'] = drop_percent

        return completed, samples
