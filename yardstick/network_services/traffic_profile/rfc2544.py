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

from trex_stl_lib.trex_stl_client import STLStream
from trex_stl_lib.trex_stl_streams import STLFlowLatencyStats
from trex_stl_lib.trex_stl_streams import STLTXCont

from yardstick.network_services.traffic_profile.traffic_profile \
    import TrexProfile

LOGGING = logging.getLogger(__name__)


class RFC2544Profile(TrexProfile):
    """ This class handles rfc2544 implemenation. """

    def __init__(self, traffic_generator):
        super(RFC2544Profile, self).__init__(traffic_generator)
        self.generator = None
        self.max_rate = None
        self.min_rate = None
        self.ports = None
        self.rate = 100
        self.drop_percent_at_max_tx = None
        self.throughput_max = None

    def register_generator(self, generator):
        self.generator = generator

    def execute(self, traffic_generator=None):
        """ Generate the stream and run traffic on the given ports """
        if traffic_generator is not None and self.generator is None:
            self.generator = traffic_generator

        if self.ports is not None:
            return

        self.ports = []
        priv_ports = self.generator.priv_ports
        pub_ports = self.generator.pub_ports
        # start from 1 for private_1, public_1, etc.
        for index, (priv_port, pub_port) in enumerate(zip(priv_ports, pub_ports), 1):
            profile_data = self.params.get('private_{}'.format(index), '')
            self.ports.append(priv_port)
            # pass profile_data directly, don't use self.profile_data
            self.generator.client.add_streams(self.get_streams(profile_data), ports=priv_port)
            profile_data = self.params.get('public_{}'.format(index), '')
            # correlated traffic doesn't use public traffic?
            if not profile_data or self.generator.rfc2544_helper.correlated_traffic:
                continue
            # just get the pub_port
            self.ports.append(pub_port)
            self.generator.client.add_streams(self.get_streams(profile_data), ports=pub_port)

        self.max_rate = self.rate
        self.min_rate = 0
        self.generator.client.start(ports=self.ports, mult=self.get_multiplier(),
                                    duration=30, force=True)
        self.drop_percent_at_max_tx = 0
        self.throughput_max = 0

    def get_multiplier(self):
        """ Get the rate at which next iteration to run """
        self.rate = round((self.max_rate + self.min_rate) / 2.0, 2)
        multiplier = round(self.rate / self.pps, 2)
        return str(multiplier)

    def get_drop_percentage(self, generator=None):
        """ Calculate the drop percentage and run the traffic """
        if generator is None:
            generator = self.generator
        run_duration = self.generator.RUN_DURATION
        samples = self.generator.generate_samples()

        in_packets = sum([value['in_packets'] for value in samples.values()])
        out_packets = sum([value['out_packets'] for value in samples.values()])

        packet_drop = abs(out_packets - in_packets)
        drop_percent = 100.0
        try:
            drop_percent = round((packet_drop / float(out_packets)) * 100, 5)
        except ZeroDivisionError:
            LOGGING.info('No traffic is flowing')

        # TODO(esm): RFC2544 doesn't tolerate packet loss, why do we?
        tolerance_low = generator.rfc2544_helper.tolerance_low
        tolerance_high = generator.rfc2544_helper.tolerance_high

        tx_rate = out_packets / run_duration
        rx_rate = in_packets / run_duration

        throughput_max = self.throughput_max
        drop_percent_at_max_tx = self.drop_percent_at_max_tx

        if self.drop_percent_at_max_tx is None:
            self.rate = tx_rate
            self.first_run = False

        if drop_percent > tolerance_high:
            # TODO(esm): why don't we discard results that are out of tolerance?
            self.max_rate = self.rate
            if throughput_max == 0:
                throughput_max = rx_rate
                drop_percent_at_max_tx = drop_percent

        elif drop_percent >= tolerance_low:
            # TODO(esm): why do we update the samples dict in this case
            #            and not update our tracking values?
            throughput_max = rx_rate
            drop_percent_at_max_tx = drop_percent

        elif drop_percent >= self.drop_percent_at_max_tx:
            # TODO(esm): why don't we discard results that are out of tolerance?
            self.min_rate = self.rate
            self.drop_percent_at_max_tx = drop_percent_at_max_tx = drop_percent
            self.throughput_max = throughput_max = rx_rate

        else:
            # TODO(esm): why don't we discard results that are out of tolerance?
            self.min_rate = self.rate

        generator.clear_client_stats()
        generator.start_client(mult=self.get_multiplier(),
                               duration=run_duration, force=True)

        # if correlated traffic update the Throughput
        if generator.rfc2544_helper.correlated_traffic:
            throughput_max *= 2

        samples.update({
            'TxThroughput': tx_rate,
            'RxThroughput': rx_rate,
            'CurrentDropPercentage': drop_percent,
            'Throughput': throughput_max,
            'DropPercentage': drop_percent_at_max_tx,
        })

        return samples

    def execute_latency(self, generator=None, samples=None):
        if generator is None:
            generator = self.generator

        if samples is None:
            samples = generator.generate_samples()

        self.pps, multiplier = self.calculate_pps(samples)
        self.ports = []
        self.pg_id = self.params['traffic_profile'].get('pg_id', 1)
        priv_ports = generator.priv_ports
        pub_ports = generator.pub_ports
        for index, (priv_port, pub_port) in enumerate(zip(priv_ports, pub_ports), 1):
            profile_data = self.params.get('private_{}'.format(index), '')
            self.ports.append(priv_port)
            generator.client.add_streams(self.get_streams(profile_data),
                                         ports=priv_port)

            profile_data = self.params.get('public_{}'.format(index), '')
            if not profile_data or generator.correlated_traffic:
                continue

            pub_port = generator.pub_ports[index]
            self.ports.append(pub_port)
            generator.client.add_streams(self.get_streams(profile_data),
                                         ports=pub_port)

        generator.start_client(ports=self.ports, mult=str(multiplier),
                               duration=120, force=True)
        self.first_run = False

    def calculate_pps(self, samples):
        pps = round(samples['Throughput'] / 2, 2)
        multiplier = round(self.rate / self.pps, 2)
        return pps, multiplier

    def create_single_stream(self, packet_size, pps, isg=0):
        packet = self._create_single_packet(packet_size)
        if pps:
            stl_mode = STLTXCont(pps=pps)
        else:
            stl_mode = STLTXCont(pps=self.pps)
        if self.pg_id:
            LOGGING.debug("pg_id: %s", self.pg_id)
            stl_flow_stats = STLFlowLatencyStats(pg_id=self.pg_id)
            stream = STLStream(isg=isg, packet=packet, mode=stl_mode,
                               flow_stats=stl_flow_stats)
            self.pg_id += 1
        else:
            stream = STLStream(isg=isg, packet=packet, mode=stl_mode)
        return stream
