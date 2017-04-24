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

from yardstick.network_services.traffic_profile.prox_profile import ProxProfile

LOG = logging.getLogger(__name__)


class ProxRampProfile(ProxProfile):
    """
    This profile adds a single stream at the beginning of the traffic session
    """
    def __init__(self, tp_config):
        super(ProxRampProfile, self).__init__(tp_config)
        self.step_value = float(self.prox_config.get('step_value', 10.0))

    def run_test_with_pkt_size(self, traffic_gen, queue, pkt_size, duration):
        """Run the test for a single packet size.

        :param traffic_gen: traffic generator instance
        :type traffic_gen: TrafficGen
        :param  pkt_size: The packet size to test with.
        :type pkt_size: int
        :param  duration: The duration for each try.
        :type duration: int

        """

        lower = self.lower_bound
        upper = self.upper_bound

        LOG.info("Testing with packet size %d", pkt_size)

        test_value = lower

        # throughput and packet loss from the last successfull test
        while test_value <= upper:
            LOG.debug("New interval [%s, %s), precision: %d", lower, upper,
                      self.step_value)
            LOG.info("Testing with value %s", test_value)

            (success, throughput, pkt_loss, rx_total, tx_total, pps, mpps,
             latency) = traffic_gen.run_test(pkt_size, duration,
                                             test_value,
                                             self.tolerated_loss)

            if success:
                LOG.debug("Success! Increasing test value")
                test_value += self.step_value
                successfull_pkt_loss = pkt_loss
            else:
                LOG.debug("Failure... stopping")
                break

            samples = self.get_samples(traffic_gen, pkt_size, mpps, pps,
                                       successfull_pkt_loss, latency)

            queue.put(samples)
