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
import datetime
import time

from yardstick.network_services.traffic_profile.prox_profile import ProxProfile

LOG = logging.getLogger(__name__)


class ProxBinSearchProfile(ProxProfile):
    """
    This profile adds a single stream at the beginning of the traffic session
    """

    def __init__(self, tp_config):
        super(ProxBinSearchProfile, self).__init__(tp_config)
        self.current_lower = self.lower_bound
        self.current_upper = self.upper_bound

    @property
    def delta(self):
        return self.current_upper - self.current_lower

    @property
    def mid_point(self):
        return (self.current_lower + self.current_upper) / 2

    def bounds_iterator(self, logger=None):
        self.current_lower = self.lower_bound
        self.current_upper = self.upper_bound

        test_value = self.current_upper
        while abs(self.delta) >= self.precision:
            if logger:
                logger.debug("New interval [%s, %s), precision: %d", self.current_lower,
                             self.current_upper, self.step_value)
                logger.info("Testing with value %s", test_value)

            yield test_value
            test_value = self.mid_point

    def run_test_with_pkt_size(self, traffic_gen, pkt_size, duration):
        """Run the test for a single packet size.

        :param traffic_gen: traffic generator instance
        :type traffic_gen: TrafficGen
        :param  pkt_size: The packet size to test with.
        :type pkt_size: int
        :param  duration: The duration for each try.
        :type duration: int

        """

        LOG.info("Testing with packet size %d", pkt_size)

        # Binary search assumes the lower value of the interval is
        # successful and the upper value is a failure.
        # The first value that is tested, is the maximum value. If that
        # succeeds, no more searching is needed. If it fails, a regular
        # binary search is performed.
        #
        # The test_value used for the first iteration of binary search
        # is adjusted so that the delta between this test_value and the
        # upper bound is a power-of-2 multiple of precision. In the
        # optimistic situation where this first test_value results in a
        # success, the binary search will complete on an integer multiple
        # of the precision, rather than on a fraction of it.

        theor_max_thruput = 0

        result_samples = {}

        # Store one time only value in influxdb
        single_samples = {
            "test_duration" : traffic_gen.scenario_helper.scenario_cfg["runner"]["duration"],
            "test_precision" : self.params["traffic_profile"]["test_precision"],
            "tolerated_loss" : self.params["traffic_profile"]["tolerated_loss"],
            "duration" : duration
        }
        self.queue.put(single_samples)
        self.prev_time = time.time()

        # throughput and packet loss from the most recent successful test
        successful_pkt_loss = 0.0
        for test_value in self.bounds_iterator(LOG):
            result, port_samples = self._profile_helper.run_test(pkt_size, duration,
                                                                 test_value, self.tolerated_loss)
            self.curr_time = time.time()
            diff_time = self.curr_time - self.prev_time
            self.prev_time = self.curr_time

            if result.success:
                LOG.debug("Success! Increasing lower bound")
                self.current_lower = test_value
                successful_pkt_loss = result.pkt_loss
                samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)
                samples["TxThroughput"] = samples["TxThroughput"] * 1000 * 1000

                # store results with success tag in influxdb
                success_samples = {'Success_' + key: value for key, value in samples.items()}

                success_samples["Success_rx_total"] = int(result.rx_total / diff_time)
                success_samples["Success_tx_total"] = int(result.tx_total / diff_time)
                success_samples["Success_can_be_lost"] = int(result.can_be_lost / diff_time)
                success_samples["Success_drop_total"] = int(result.drop_total / diff_time)
                self.queue.put(success_samples)

                # Store Actual throughput for result samples
                result_samples["Result_Actual_throughput"] = \
                    success_samples["Success_RxThroughput"]
            else:
                LOG.debug("Failure... Decreasing upper bound")
                self.current_upper = test_value
                samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)

            for k in samples:
                    tmp = samples[k]
                    if isinstance(tmp, dict):
                        for k2 in tmp:
                            samples[k][k2] = int(samples[k][k2] / diff_time)

            if theor_max_thruput < samples["TxThroughput"]:
                theor_max_thruput = samples['TxThroughput']
                self.queue.put({'theor_max_throughput': theor_max_thruput})

            LOG.debug("Collect TG KPIs %s %s", datetime.datetime.now(), samples)
            self.queue.put(samples)

        result_samples["Result_pktSize"] = pkt_size
        result_samples["Result_theor_max_throughput"] = theor_max_thruput/ (1000 * 1000)
        self.queue.put(result_samples)
