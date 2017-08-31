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

from __future__ import absolute_import
import logging
import json

from yardstick.network_services.traffic_profile.traffic_profile import \
    TrexProfile

LOG = logging.getLogger(__name__)


class IXIARFC2544Profile(TrexProfile):
    def _get_ixia_traffic_profile(self, profile_data, mac={},
                                  xfile=None, static_traffic={}):
        result = {}
        if xfile:
            with open(xfile, 'r') as stream:
                try:
                    static_traffic = json.load(stream)
                except Exception as exc:
                    LOG.debug(exc)

        for traffickey, trafficvalue in static_traffic.items():
            traffic = static_traffic[traffickey]
            # outer_l2
            index = 0
            for key, value in profile_data[traffickey].items():
                framesize = value['outer_l2']['framesize']
                traffic['outer_l2']['framesize'] = framesize
                traffic['framesPerSecond'] = True
                traffic['bidir'] = False
                traffic['outer_l2']['srcmac'] = \
                    mac["src_mac_{}".format(traffic['id'])]
                traffic['outer_l2']['dstmac'] = \
                    mac["dst_mac_{}".format(traffic['id'])]
                # outer_l3
                if "outer_l3v6" in list(value.keys()):
                    traffic['outer_l3'] = value['outer_l3v6']
                    srcip4 = value['outer_l3v6']['srcip6']
                    traffic['outer_l3']['srcip4'] = srcip4.split("-")[0]
                    dstip4 = value['outer_l3v6']['dstip6']
                    traffic['outer_l3']['dstip4'] = dstip4.split("-")[0]
                else:
                    traffic['outer_l3'] = value['outer_l3v4']
                    srcip4 = value['outer_l3v4']['srcip4']
                    traffic['outer_l3']['srcip4'] = srcip4.split("-")[0]
                    dstip4 = value['outer_l3v4']['dstip4']
                    traffic['outer_l3']['dstip4'] = dstip4.split("-")[0]

                traffic['outer_l3']['type'] = key
                traffic['outer_l3']['count'] = value['outer_l3v4']['count']
                # outer_l4
                traffic['outer_l4'] = value['outer_l4']
                index = index + 1
            result.update({traffickey: traffic})

        return result

    def _ixia_traffic_generate(self, traffic_generator, traffic, ixia_obj):
        for key, value in traffic.items():
            if "public" in key or "private" in key:
                traffic[key]["iload"] = str(self.rate)
        ixia_obj.ix_update_frame(traffic)
        ixia_obj.ix_update_ether(traffic)
        ixia_obj.add_ip_header(traffic, 4)
        ixia_obj.ix_start_traffic()
        self.tmp_drop = 0
        self.tmp_throughput = 0

    def execute(self, traffic_generator, ixia_obj, mac={}, xfile=None):
        if self.first_run:
            self.full_profile = {}
            self.pg_id = 0
            self.profile = 'private_1'
            for key, value in self.params.items():
                if "private" in key or "public" in key:
                    self.profile_data = self.params[key]
                    self.get_streams(self.profile_data)
                    self.full_profile.update({key: self.profile_data})
            traffic = \
                self._get_ixia_traffic_profile(self.full_profile, mac, xfile)
            self.max_rate = self.rate
            self.min_rate = 0
            self.get_multiplier()
            self._ixia_traffic_generate(traffic_generator, traffic, ixia_obj)

    def get_multiplier(self):
        self.rate = round((self.max_rate + self.min_rate) / 2.0, 2)
        multiplier = round(self.rate / self.pps, 2)
        return str(multiplier)

    def start_ixia_latency(self, traffic_generator, ixia_obj,
                           mac={}, xfile=None):
        traffic = self._get_ixia_traffic_profile(self.full_profile, mac)
        self._ixia_traffic_generate(traffic_generator, traffic,
                                    ixia_obj, xfile)

    def get_drop_percentage(self, traffic_generator, samples, tol_min,
                            tolerance, ixia_obj, mac={}, xfile=None):
        status = 'Running'
        drop_percent = 100
        in_packets = sum([samples[iface]['in_packets'] for iface in samples])
        out_packets = sum([samples[iface]['out_packets'] for iface in samples])
        rx_throughput = \
            sum([samples[iface]['RxThroughput'] for iface in samples])
        tx_throughput = \
            sum([samples[iface]['TxThroughput'] for iface in samples])
        packet_drop = abs(out_packets - in_packets)
        try:
            drop_percent = round((packet_drop / float(out_packets)) * 100, 2)
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
        if self.first_run:
            max_supported_rate = out_packets / 30.0
            self.rate = max_supported_rate
            self.first_run = False
            if drop_percent <= tolerance:
                status = 'Completed'
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
            return status, samples
        self.get_multiplier()
        traffic = self._get_ixia_traffic_profile(self.full_profile, mac, xfile)
        self._ixia_traffic_generate(traffic_generator, traffic, ixia_obj)
        return status, samples
