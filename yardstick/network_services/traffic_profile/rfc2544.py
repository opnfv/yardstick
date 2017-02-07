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
""" RFC2544 Throughput implemenation """

from __future__ import absolute_import
from __future__ import division
import logging

from yardstick.network_services.traffic_profile.traffic_profile \
    import TrexProfile

LOGGING = logging.getLogger(__name__)


class RFC2544Profile(TrexProfile):
    """ This class handles rfc2544 implemenation. """

    def __init__(self, traffic_generator):
        super(RFC2544Profile, self).__init__(traffic_generator)
        self.max_rate = None
        self.min_rate = None
        self.rate = 100
        self.tmp_drop = None
        self.tmp_throughput = None
        self.profile_data = None

    def execute(self, traffic_generator):
        ''' Generate the stream and run traffic on the given ports '''
        if self.first_run:
            self.profile_data = self.params.get('private', '')
            ports = [traffic_generator.my_ports[0]]
            traffic_generator.client.add_streams(self.get_streams(),
                                                 ports=ports[0])
            profile_data = self.params.get('public', '')
            if profile_data:
                self.profile_data = profile_data
                ports.append(traffic_generator.my_ports[1])
                traffic_generator.client.add_streams(self.get_streams(),
                                                     ports=ports[1])

            self.max_rate = self.rate
            self.min_rate = 0
            traffic_generator.client.start(ports=ports,
                                           mult=self.get_multiplier(),
                                           duration=30, force=True)
            self.tmp_drop = 0
            self.tmp_throughput = 0

    def get_multiplier(self):
        ''' Get the rate at which next iternation to run '''
        self.rate = round((self.max_rate + self.min_rate) / 2.0, 2)
        multiplier = round(self.rate / self.pps, 2)
        return str(multiplier)

    def get_drop_percentage(self, traffic_generator,
                            samples, tol_min, tolerance):
        ''' Calculate the drop percentage and run the traffic '''
        in_packets = sum([samples[iface]['in_packets'] for iface in samples])
        out_packets = sum([samples[iface]['out_packets'] for iface in samples])
        packet_drop = abs(out_packets - in_packets)
        drop_percent = 100.0
        try:
            drop_percent = round((packet_drop / float(out_packets)) * 100, 2)
        except ZeroDivisionError:
            LOGGING.info('No traffic is flowing')
        samples['TxThroughput'] = out_packets / 30
        samples['RxThroughput'] = in_packets / 30
        samples['CurrentDropPercentage'] = drop_percent
        samples['Throughput'] = self.tmp_throughput
        samples['DropPercentage'] = self.tmp_drop
        if drop_percent > tolerance and self.tmp_throughput == 0:
            samples['Throughput'] = (in_packets / 30)
            samples['DropPercentage'] = drop_percent
        if self.first_run:
            max_supported_rate = out_packets / 30
            self.rate = max_supported_rate
            self.first_run = False
        if drop_percent > tolerance:
            self.max_rate = self.rate
        elif drop_percent < tol_min:
            self.min_rate = self.rate
            if drop_percent >= self.tmp_drop:
                self.tmp_drop = drop_percent
                self.tmp_throughput = (in_packets / 30)
                samples['Throughput'] = (in_packets / 30)
                samples['DropPercentage'] = drop_percent
        else:
            samples['Throughput'] = (in_packets / 30)
            samples['DropPercentage'] = drop_percent

        traffic_generator.client.clear_stats(ports=traffic_generator.my_ports)
        traffic_generator.client.start(ports=traffic_generator.my_ports,
                                       mult=self.get_multiplier(),
                                       duration=30, force=True)
        return samples
