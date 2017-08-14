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

        for test_value in self.bounds_iterator(LOG):
            test_result = traffic_gen.resource_helper.run_test(pkt_size, duration,
                                                               test_value, self.tolerated_loss)

            if not test_result.success:
                LOG.debug("Failure... stopping")
                break

            LOG.debug("Success! Increasing test value")
            samples = test_result.get_samples(pkt_size)
            self.fill_samples(samples, traffic_gen)

            self.queue.put(samples)
