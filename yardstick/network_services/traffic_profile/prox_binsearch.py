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
from yardstick.network_services import constants
from yardstick.common import constants as overall_constants

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

        theor_max_thruput = actual_max_thruput = 0

        result_samples = {}
        rate_samples = {}
        pos_retry = 0
        neg_retry = 0
        total_retry = 0
        ok_retry = 0

        # Store one time only value in influxdb
        single_samples = {
            "test_duration": traffic_gen.scenario_helper.scenario_cfg["runner"]["duration"],
            "test_precision": self.precision,
            "tolerated_loss": self.tolerated_loss,
            "duration": duration
        }
        self.queue.put(single_samples)
        self.prev_time = time.time()

        # throughput and packet loss from the most recent successful test
        successful_pkt_loss = 0.0
        line_speed = traffic_gen.scenario_helper.all_options.get(
            "interface_speed_gbps", constants.NIC_GBPS_DEFAULT) * constants.ONE_GIGABIT_IN_BITS

        ok_retry = traffic_gen.scenario_helper.scenario_cfg["runner"].get("confirmation", 0)
        for test_value in self.bounds_iterator(LOG):
            pos_retry = 0
            neg_retry = 0
            total_retry = 0

            rate_samples["MAX_Rate"] = self.current_upper
            rate_samples["MIN_Rate"] = self.current_lower
            rate_samples["Test_Rate"] = test_value
            self.queue.put(rate_samples, True, overall_constants.QUEUE_PUT_TIMEOUT)
            LOG.info("Checking MAX %s MIN %s TEST %s",
                self.current_upper, self.lower_bound, test_value)
            while (pos_retry <= ok_retry) and (neg_retry <= ok_retry):

                total_retry = total_retry + 1
                result, port_samples = self._profile_helper.run_test(pkt_size, duration,
                                                                     test_value,
                                                                     self.tolerated_loss,
                                                                     line_speed)
                if (total_retry > (ok_retry * 3)) and (ok_retry is not 0):
                    LOG.info("Failure.!! .. RETRY EXCEEDED ... decrease lower bound")

                    successful_pkt_loss = result.pkt_loss
                    samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)

                    self.current_upper = test_value
                    neg_retry = total_retry
                elif result.success:
                    if (pos_retry < ok_retry) and (ok_retry is not 0):
                        neg_retry = 0
                        LOG.info("Success! ... confirm retry")

                        successful_pkt_loss = result.pkt_loss
                        samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)

                    else:
                        LOG.info("Success! Increasing lower bound")
                        self.current_lower = test_value

                        successful_pkt_loss = result.pkt_loss
                        samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)

                        # store results with success tag in influxdb
                        success_samples = \
                            {'Success_' + key: value for key, value in samples.items()}

                        success_samples["Success_rx_total"] = int(result.rx_total)
                        success_samples["Success_tx_total"] = int(result.tx_total)
                        success_samples["Success_can_be_lost"] = int(result.can_be_lost)
                        success_samples["Success_drop_total"] = int(result.drop_total)
                        success_samples["Success_RxThroughput"] = samples["RxThroughput"]
                        success_samples["Success_RxThroughput_gbps"] = \
                            (samples["RxThroughput"] / 1000) * ((pkt_size + 20)* 8)
                        LOG.info(">>>##>>Collect SUCCESS TG KPIs %s %s",
                                 datetime.datetime.now(), success_samples)
                        self.queue.put(success_samples, True, overall_constants.QUEUE_PUT_TIMEOUT)

                        # Store Actual throughput for result samples
                        actual_max_thruput = success_samples["Success_RxThroughput"]

                    pos_retry = pos_retry + 1

                else:
                    if (neg_retry < ok_retry) and (ok_retry is not 0):

                        pos_retry = 0
                        LOG.info("failure! ... confirm retry")
                    else:
                        LOG.info("Failure... Decreasing upper bound")
                        self.current_upper = test_value

                    neg_retry = neg_retry + 1
                    samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)

                if theor_max_thruput < samples["TxThroughput"]:
                    theor_max_thruput = samples['TxThroughput']
                    self.queue.put({'theor_max_throughput': theor_max_thruput})

                LOG.info(">>>##>>Collect TG KPIs %s %s", datetime.datetime.now(), samples)
                self.queue.put(samples, True, overall_constants.QUEUE_PUT_TIMEOUT)

        LOG.info(">>>##>> Result Reached PktSize %s Theor_Max_Thruput %s Actual_throughput %s",
                 pkt_size, theor_max_thruput, actual_max_thruput)
        result_samples["Result_pktSize"] = pkt_size
        result_samples["Result_theor_max_throughput"] = theor_max_thruput
        result_samples["Result_Actual_throughput"] = actual_max_thruput
        self.queue.put(result_samples)
