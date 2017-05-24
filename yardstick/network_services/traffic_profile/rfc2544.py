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

from stl.trex_stl_lib.trex_stl_client import STLStream
from stl.trex_stl_lib.trex_stl_streams import STLFlowLatencyStats
from stl.trex_stl_lib.trex_stl_streams import STLTXCont

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
            self.ports = []
            for index, priv_port in enumerate(traffic_generator.priv_ports):
                self.profile_data = \
                    self.params.get('private_%s' % str(index + 1), '')
                self.ports.append(traffic_generator.priv_ports[index])
                privports = traffic_generator.priv_ports[index]
                traffic_generator.client.add_streams(self.get_streams(),
                                                     ports=privports)
                profile_data = \
                    self.params.get('public_%s' % str(index + 1), '')
                if profile_data:
                    self.profile_data = profile_data
                    self.ports.append(traffic_generator.pub_ports[index])
                    pubports = traffic_generator.pub_ports[index]
                    traffic_generator.client.add_streams(self.get_streams(),
                                                         ports=pubports)

            self.max_rate = self.rate
            self.min_rate = 0
            traffic_generator.client.start(ports=self.ports,
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

    def execute_latency(self, traffic_generator, samples):
        self.pps, multiplier = self.calculate_pps(samples)
        self.ports = []
        self.pg_id = self.params['traffic_profile'].get('pg_id', 1)
        for index, priv_port in enumerate(traffic_generator.priv_ports):
            self.profile_data = \
                self.params.get('private_%s' % str(index + 1), '')
            self.ports.append(traffic_generator.priv_ports[index])
            privports = traffic_generator.priv_ports[index]
            traffic_generator.client.add_streams(self.get_streams(),
                                                 ports=privports)
            profile_data = \
                self.params.get('public_%s' % str(index + 1), '')
            if profile_data:
                self.profile_data = profile_data
                self.ports.append(traffic_generator.pub_ports[index])
                pubports = traffic_generator.pub_ports[index]
                traffic_generator.client.add_streams(self.get_streams(),
                                                     ports=pubports)
        traffic_generator.client.start(mult=str(multiplier),
                                       ports=self.ports,
                                       duration=120, force=True)
        self.first_run = False
        self.traffic_gen = None

    def calculate_pps(self, samples):
        pps = round(samples['Throughput'] / 2, 2)
        multiplier = round(self.rate / self.pps, 2)
        return [pps, multiplier]

    def create_single_stream(self, packet_size, pps, isg=0):
        packet = self.create_single_packet(packet_size)
        if self.pg_id:
            LOGGING.debug("pg_id: %s", self.pg_id)
            stream = STLStream(
                isg=isg, packet=packet, mode=STLTXCont(pps=self.pps),
                flow_stats=STLFlowLatencyStats(pg_id=self.pg_id))
            self.pg_id += 1
        else:
            stream = STLStream(
                isg=isg, packet=packet, mode=STLTXCont(pps=self.pps))
        return stream
