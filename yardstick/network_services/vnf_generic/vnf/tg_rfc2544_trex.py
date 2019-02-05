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

from six import moves
from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import tg_trex
from trex_stl_lib.trex_stl_exceptions import STLError


LOG = logging.getLogger(__name__)


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
            self.rfc2544_helper.correlated_traffic,
            self.rfc2544_helper.resolution)
        self._queue.put(output)
        return completed

    def start_client(self, ports, mult=None, duration=None, force=True):
        self.client.start(ports=ports, mult=mult, duration=duration, force=force)

    def clear_client_stats(self, ports):
        self.client.clear_stats(ports=ports)

    def run_test(self, traffic_profile, tasks_queue, results_queue, *args): # pragma: no cover
        LOG.debug("Trex resource_helper run_test")
        if self._terminated.value:
            return
        # if we don't do this we can hang waiting for the queue to drain
        # have to do this in the subprocess
        self._queue.cancel_join_thread()
        try:
            self._build_ports()
            self.client = self._connect()
            self.client.reset(ports=self.all_ports)
            self.client.remove_all_streams(self.all_ports)  # remove all streams
            traffic_profile.register_generator(self)

            completed = False
            self.rfc2544_helper.iteration.value = 0
            self.client_started.value = 1
            while completed is False and not self._terminated.value:
                LOG.debug("Wait for task ...")
                try:
                    task = tasks_queue.get(True, 5)
                except moves.queue.Empty:
                    LOG.debug("Wait for task timeout, continue waiting...")
                    continue
                else:
                    if task != 'RUN_TRAFFIC':
                        continue
                self.rfc2544_helper.iteration.value += 1
                LOG.info("Got %s task, start iteration %d", task,
                         self.rfc2544_helper.iteration.value)
                completed = self._run_traffic_once(traffic_profile)
                if completed:
                    LOG.debug("%s::run_test - test completed",
                              self.__class__.__name__)
                    results_queue.put('COMPLETE')
                else:
                    results_queue.put('CONTINUE')
                tasks_queue.task_done()

            self.client.stop(self.all_ports)
            self.client.disconnect()
            self._terminated.value = 0
        except STLError:
            if self._terminated.value:
                LOG.debug("traffic generator is stopped")
                return  # return if trex/tg server is stopped.
            raise

        self.client_started.value = 0
        LOG.debug("%s::run_test done", self.__class__.__name__)

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
