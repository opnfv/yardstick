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

from yardstick.network_services.traffic_profile.base import TrafficProfile

LOG = logging.getLogger(__name__)


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

    def execute(self, traffic_generator):
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
