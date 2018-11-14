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

from yardstick.network_services.traffic_profile.prox_profile import ProxProfile

LOG = logging.getLogger(__name__)


class ProxIrqProfile(ProxProfile):
    """
    This profile adds a single stream at the beginning of the traffic session
    """

    def __init__(self, tp_config):
        super(ProxIrqProfile, self).__init__(tp_config)

    def init(self, queue):
        self.queue = queue
        self.queue.cancel_join_thread()

    def execute_traffic(self, traffic_generator):
        LOG.debug("Prox_IRQ Execute Traffic....")
        time.sleep(20)

    def is_ended(self):
        return False

    def run_test(self):
        """Run the test
        """

        LOG.info("Prox_IRQ ....")
