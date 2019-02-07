# Copyright (c) 2016-2019 Intel Corporation
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

import logging
import time

from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import tg_trex


LOGGING = logging.getLogger(__name__)


class TrexRfcResourceHelper(tg_trex.TrexResourceHelper):

    SAMPLING_PERIOD = 2
    TRANSIENT_PERIOD = 10

    def __init__(self, setup_helper):
        super(TrexRfcResourceHelper, self).__init__(setup_helper)
        self.rfc2544_helper = sample_vnf.Rfc2544ResourceHelper(
            self.scenario_helper)

    def _run_traffic_once(self, traffic_profile):
        self.client_started.value = 1
        ports, port_pg_id = traffic_profile.execute_traffic(self)

        samples = []
        timeout = int(traffic_profile.config.duration) - self.TRANSIENT_PERIOD
        time.sleep(self.TRANSIENT_PERIOD)
        for _ in utils.Timer(timeout=timeout):
            samples.append(self._get_samples(ports, port_pg_id=port_pg_id))
            time.sleep(self.SAMPLING_PERIOD)

        traffic_profile.stop_traffic(self)
        completed, output = traffic_profile.get_drop_percentage(
            samples, self.rfc2544_helper.tolerance_low,
            self.rfc2544_helper.tolerance_high,
            self.rfc2544_helper.correlated_traffic)
        self._queue.put(output)
        return completed

    def start_client(self, ports, mult=None, duration=None, force=True):
        self.client.start(ports=ports, mult=mult, duration=duration, force=force)

    def clear_client_stats(self, ports):
        self.client.clear_stats(ports=ports)


class TrexTrafficGenRFC(tg_trex.TrexTrafficGen):
    """
    This class handles mapping traffic profile and generating
    traffic for rfc2544 testcase.
    """

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if resource_helper_type is None:
            resource_helper_type = TrexRfcResourceHelper

        super(TrexTrafficGenRFC, self).__init__(name, vnfd, setup_env_helper_type,
                                                resource_helper_type)
