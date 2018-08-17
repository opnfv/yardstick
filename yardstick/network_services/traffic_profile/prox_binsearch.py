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

STATUS_SUCCESS = "Success"
STATUS_FAIL = "Failure"
STATUS_RESULT = "Result"
STEP_CONFIRM = "Confirm retry"
STEP_INCREASE_LOWER = "Increase lower"
STEP_DECREASE_LOWER = "Decrease lower"
STEP_DECREASE_UPPER = "Decrease upper"


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

        test_data = {
            "test_duration": traffic_gen.scenario_helper.scenario_cfg["runner"]["duration"],
            "test_precision": self.params["traffic_profile"]["test_precision"],
            "tolerated_loss": self.params["traffic_profile"]["tolerated_loss"],
            "duration": duration
        }
        self.prev_time = time.time()

        # throughput and packet loss from the most recent successful test
        successful_pkt_loss = 0.0
        line_speed = traffic_gen.scenario_helper.all_options.get(
            "interface_speed_gbps", constants.NIC_GBPS_DEFAULT) * constants.ONE_GIGABIT_IN_BITS

        ok_retry = traffic_gen.scenario_helper.scenario_cfg["runner"].get("confirmation", 0)
        for step_id, test_value in enumerate(self.bounds_iterator(LOG)):
            pos_retry = 0
            neg_retry = 0
            total_retry = 0

            LOG.info("Checking MAX %s MIN %s TEST %s", self.current_upper,
                     self.lower_bound, test_value)

            while (pos_retry <= ok_retry) and (neg_retry <= ok_retry):

                total_retry = total_retry + 1

                result, port_samples = self._profile_helper.run_test(pkt_size, duration,
                                                                     test_value,
                                                                     self.tolerated_loss,
                                                                     line_speed)

                if (total_retry > (ok_retry * 3)) and (ok_retry is not 0):
                    status = STATUS_FAIL
                    next_step = STEP_DECREASE_LOWER
                    successful_pkt_loss = result.pkt_loss
                    self.current_upper = test_value
                    neg_retry = total_retry
                elif result.success:
                    if (pos_retry < ok_retry) and (ok_retry is not 0):
                        status = STATUS_SUCCESS
                        next_step = STEP_CONFIRM
                        successful_pkt_loss = result.pkt_loss
                        neg_retry = 0
                    else:
                        status = STATUS_SUCCESS
                        next_step = STEP_INCREASE_LOWER
                        self.current_lower = test_value
                        successful_pkt_loss = result.pkt_loss

                    pos_retry = pos_retry + 1

                else:
                    if (neg_retry < ok_retry) and (ok_retry is not 0):
                        status = STATUS_FAIL
                        next_step = STEP_CONFIRM
                        pos_retry = 0
                    else:
                        status = STATUS_FAIL
                        next_step = STEP_DECREASE_UPPER
                        self.current_upper = test_value

                    neg_retry = neg_retry + 1

                LOG.info(
                    "Status = '%s' Next_Step = '%s'", status, next_step)

                samples = result.get_samples(pkt_size, successful_pkt_loss, port_samples)

                if theor_max_thruput < samples["TxThroughput"]:
                    theor_max_thruput = samples['TxThroughput']
                samples['theor_max_throughput'] = theor_max_thruput

                samples["rx_total"] = int(result.rx_total)
                samples["tx_total"] = int(result.tx_total)
                samples["can_be_lost"] = int(result.can_be_lost)
                samples["drop_total"] = int(result.drop_total)
                samples["RxThroughput_gbps"] = \
                    (samples["RxThroughput"] / 1000) * ((pkt_size + 20) * 8)
                samples['Status'] = status
                samples['Next_Step'] = next_step
                samples["MAX_Rate"] = self.current_upper
                samples["MIN_Rate"] = self.current_lower
                samples["Test_Rate"] = test_value
                samples["Step_Id"] = step_id
                samples["Confirmation_Retry"] = total_retry

                samples.update(test_data)

                if status == STATUS_SUCCESS and next_step == STEP_INCREASE_LOWER:
                    # Store success samples for result samples
                    result_samples = samples

                LOG.info(">>>##>>Collect TG KPIs %s %s", datetime.datetime.now(), samples)

                self.queue.put(samples, True, overall_constants.QUEUE_PUT_TIMEOUT)

        LOG.info(
            ">>>##>> Result Reached PktSize %s Theor_Max_Thruput %s Actual_throughput %s",
            pkt_size, theor_max_thruput, result_samples.get("RxThroughput", 0))
        result_samples["Status"] = STATUS_RESULT
        result_samples["Next_Step"] = ""
        result_samples["Actual_throughput"] = result_samples.get("RxThroughput", 0)
        result_samples["theor_max_throughput"] = theor_max_thruput
        self.queue.put(result_samples)
