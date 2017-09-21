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
""" Fixed traffic profile definitions """

from __future__ import absolute_import

import logging

import time

from collections import namedtuple

from yardstick.network_services.traffic_profile.base import TrafficProfile

LOG = logging.getLogger(__name__)


class ProxTestDataTuple(namedtuple('ProxTestDataTuple', 'tolerated,tsc_hz,delta_rx,'
                                                        'delta_tx,delta_tsc,'
                                                        'latency,rx_total,tx_total,pps')):

    @property
    def pkt_loss(self):
        try:
            return 1e2 * self.drop_total / float(self.tx_total)
        except ZeroDivisionError:
            return 100.0

    @property
    def mpps(self):
        # calculate the effective throughput in Mpps
        return float(self.delta_tx) * self.tsc_hz / self.delta_tsc / 1e6

    @property
    def can_be_lost(self):
        return int(self.tx_total * self.tolerated / 1e2)

    @property
    def drop_total(self):
        return self.tx_total - self.rx_total

    @property
    def success(self):
        return self.drop_total <= self.can_be_lost

    def get_samples(self, pkt_size, pkt_loss=None, port_samples=None):
        if pkt_loss is None:
            pkt_loss = self.pkt_loss

        if port_samples is None:
            port_samples = {}

        latency_keys = [
            "LatencyMin",
            "LatencyMax",
            "LatencyAvg",
        ]

        samples = {
            "Throughput": self.mpps,
            "DropPackets": pkt_loss,
            "CurrentDropPackets": pkt_loss,
            "TxThroughput": self.pps / 1e6,
            "RxThroughput": self.mpps,
            "PktSize": pkt_size,
        }
        if port_samples:
            samples.update(port_samples)

        samples.update((key, value) for key, value in zip(latency_keys, self.latency))
        return samples

    def log_data(self, logger=None):
        if logger is None:
            logger = LOG

        template = "RX: %d; TX: %d; dropped: %d (tolerated: %d)"
        logger.debug(template, self.rx_total, self.tx_total, self.drop_total, self.can_be_lost)
        logger.debug("Mpps configured: %f; Mpps effective %f", self.pps / 1e6, self.mpps)


class ProxProfile(TrafficProfile):
    """
    This profile adds a single stream at the beginning of the traffic session
    """

    @staticmethod
    def fill_samples(samples, traffic_gen):
        for vpci_idx, intf in enumerate(traffic_gen.vpci_if_name_ascending):
            name = intf[1]
            # TODO: VNFDs KPIs values needs to be mapped to TRex structure
            xe_port = traffic_gen.resource_helper.sut.port_stats([vpci_idx])
            samples[name] = {
                "in_packets": xe_port[6],
                "out_packets": xe_port[7],
            }

    def __init__(self, tp_config):
        super(ProxProfile, self).__init__(tp_config)
        self.queue = None
        self.done = False
        self.results = []

        # TODO: get init values from tp_config
        self.prox_config = tp_config["traffic_profile"]
        self.pkt_sizes = [int(x) for x in self.prox_config.get("packet_sizes", [])]
        self.pkt_size_iterator = iter(self.pkt_sizes)
        self.duration = int(self.prox_config.get("duration", 5))
        self.precision = float(self.prox_config.get('test_precision', 1.0))
        self.tolerated_loss = float(self.prox_config.get('tolerated_loss', 0.0))

        # TODO: is this ever a function of packet size?
        self.lower_bound = float(self.prox_config.get('lower_bound', 10.0))
        self.upper_bound = float(self.prox_config.get('upper_bound', 100.0))
        self.step_value = float(self.prox_config.get('step_value', 10.0))

    def init(self, queue):
        self.pkt_size_iterator = iter(self.pkt_sizes)
        self.queue = queue

    def bounds_iterator(self, logger=None):
        if logger:
            logger.debug("Interval [%s, %s), step: %d", self.lower_bound,
                         self.upper_bound, self.step_value)

        test_value = self.lower_bound
        while test_value <= self.upper_bound:
            if logger:
                logger.info("Testing with value %s", test_value)
            yield test_value
            test_value += self.step_value

    @property
    def min_pkt_size(self):
        """Return the minimum required packet size for the test.

        Defaults to 64. Individual test must override this method if they have
        other requirements.

        Returns:
            int. The minimum required packet size for the test.
        """
        return 64

    def run_test_with_pkt_size(self, traffic_generator, pkt_size, duration):
        raise NotImplementedError

    def execute_traffic(self, traffic_generator):
        try:
            pkt_size = next(self.pkt_size_iterator)
        except StopIteration:
            self.done = True
            return

        # Adjust packet size upwards if it's less than the minimum
        # required packet size for the test.
        if pkt_size < self.min_pkt_size:
            pkt_size += self.min_pkt_size - 64

        duration = self.duration
        self.run_test_with_pkt_size(traffic_generator, pkt_size, duration)

    def run_test(self, traffic_gen, pkt_size, duration, value, tolerated_loss=0.0):
        # do this assert in init?  unless we expect interface count to
        # change from one run to another run...
        ports = traffic_gen.vnfd_helper.port_pairs.all_ports
        port_count = len(ports)
        assert port_count in {1, 2, 4}, \
            "Invalid number of ports: 1, 2 or 4 ports only supported at this time"

        with traffic_gen.traffic_context(pkt_size, value):
            # Getting statistics to calculate PPS at right speed....
            tsc_hz = float(traffic_gen.sut.hz())
            time.sleep(2)
            with traffic_gen.sut.measure_tot_stats() as data:
                time.sleep(duration)

            # Get stats before stopping the cores. Stopping cores takes some time
            # and might skew results otherwise.
            latency = traffic_gen.get_latency()

        deltas = data['delta']
        rx_total, tx_total = traffic_gen.sut.port_stats(range(port_count))[6:8]
        pps = value / 100.0 * traffic_gen.line_rate_to_pps(pkt_size, port_count)

        samples = {}
        # we are currently using enumeration to map logical port num to interface
        for port_name in ports:
            port = traffic_gen.vnfd_helper.port_num(port_name)
            port_rx_total, port_tx_total = traffic_gen.sut.port_stats([port])[6:8]
            samples[port_name] = {
                "in_packets": port_rx_total,
                "out_packets": port_tx_total,
            }

        result = ProxTestDataTuple(tolerated_loss, tsc_hz, deltas.rx, deltas.tx,
                                   deltas.tsc, latency, rx_total, tx_total, pps)
        result.log_data()
        return result, samples
