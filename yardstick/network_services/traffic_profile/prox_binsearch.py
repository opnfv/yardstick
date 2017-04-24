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


class ProxBinSearchProfile(ProxProfile):
    """
    This profile adds a single stream at the beginning of the traffic session
    """
    def __init__(self, tp_config):
        super(ProxBinSearchProfile, self).__init__(tp_config)

    def run_test_with_pkt_size(self, traffic_gen, queue, pkt_size, duration):
        """Run the test for a single packet size.

        :param queue: queue object we put samples into
        :type queue: Queue
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

        # Binary search assumes the lower value of the interval is
        # successful and the upper value is a failure.
        # The first value that is tested, is the maximum value. If that
        # succeeds, no more searching is needed. If it fails, a regular
        # binary search is performed.
        # The test_value used for the first iteration of binary search
        # is adjusted so that the delta between this test_value and the
        # upper bound is a power-of-2 multiple of precision. In the
        # optimistic situation where this first test_value results in a
        # success, the binary search will complete on an integer multiple
        # of the precision, rather than on a fraction of it.
        adjust = self.calc_adjust(upper, lower, self.precision)

        test_value = upper
        delta = upper - lower

        # throughput and packet loss from the last successfull test
        successfull_pkt_loss = 0.0
        while delta >= self.precision:
            LOG.debug("New interval [%s, %s), precision: %d", lower, upper,
                      upper - lower)
            LOG.info("Testing with value %s", test_value)

            (success, throughput, pkt_loss, rx_total, tx_total, pps, mpps,
             latency) = traffic_gen.run_test(pkt_size, duration,
                                             test_value,
                                             self.tolerated_loss)

            if success:
                LOG.debug("Success! Increasing lower bound")
                lower = test_value
                successfull_pkt_loss = pkt_loss
            else:
                LOG.debug("Failure... Decreasing upper bound")
                upper = test_value

            delta = upper - lower
            test_value = lower + (delta) / 2.0 + adjust
            adjust = 0.0

            samples = self.get_samples(traffic_gen, pkt_size, mpps, pps,
                                       successfull_pkt_loss, latency)

            queue.put(samples)

    @staticmethod
    def calc_adjust(upper, lower, precision):
        adjust = precision
        delta = upper - lower
        while delta > adjust:
            adjust *= 2
        adjust = (delta - adjust) / 2.0
        return adjust
