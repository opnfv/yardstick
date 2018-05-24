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

from collections import Mapping
import logging
import time

from yardstick.common import utils
from yardstick.network_services.vnf_generic.vnf import sample_vnf
from yardstick.network_services.vnf_generic.vnf import tg_trex


LOGGING = logging.getLogger(__name__)


class TrexRfcResourceHelper(tg_trex.TrexResourceHelper):

    #LATENCY_TIME_SLEEP = 120
    #RUN_DURATION = 30
    #WAIT_TIME = 3
    SAMPLING_PERIOD = 2

    def __init__(self, setup_helper):
        super(TrexRfcResourceHelper, self).__init__(setup_helper)
        self.rfc2544_helper = sample_vnf.Rfc2544ResourceHelper(
            self.scenario_helper)


    def _run_traffic_once(self, traffic_profile):
        # if self._terminated.value:
        #     return

        # Start traffic (tp.execute_traffic), capture stats during traffic injection (throughput and
        # latency) and calculate KPIs (including drop percentage)


        port_pg_id = traffic_profile.execute_traffic(self)
        with utils.Timer(timeout=traffic_profile.config.duration,
                         raise_exception=False):
            time.sleep(self.SAMPLING_PERIOD)
            self._get_samples(port_pg_id=port_pg_id)

        traffic_profile.stop_traffic(self)


        for i in range(10):
            time.sleep(1)
            a = self._get_samples(port_pg_id=port_pg_id)


        self.client_started.value = 1
        time.sleep(self.RUN_DURATION)
        self.client.stop(traffic_profile.ports)
        time.sleep(self.WAIT_TIME)
        samples = traffic_profile.get_drop_percentage(self)
        self._queue.put(samples)

        # if not self.rfc2544_helper.is_done():
        #     return

        self.client.stop(traffic_profile.ports)
        self.client.reset(ports=traffic_profile.ports)
        self.client.remove_all_streams(traffic_profile.ports)
        traffic_profile.execute_traffic_latency(samples=samples)
        multiplier = traffic_profile.calculate_pps(samples)[1]
        for _ in range(5):
            time.sleep(self.LATENCY_TIME_SLEEP)
            self.client.stop(traffic_profile.ports)
            time.sleep(self.WAIT_TIME)
            last_res = self.client.get_stats(traffic_profile.ports)
            if not isinstance(last_res, Mapping):
                self._terminated.value = 1
                continue
            self.generate_samples(traffic_profile.ports, 'latency', {})
            self._queue.put(samples)
            self.client.start(mult=str(multiplier),
                              ports=traffic_profile.ports,
                              duration=120, force=True)




    def get_drop_percentage(self, generator=None):
        """ Calculate the drop percentage and run the traffic """
        if generator is None:
            generator = self.generator
        run_duration = self.generator.RUN_DURATION
        samples = self.generator.generate_samples(self.ports)

        # in_packets = sum([value['in_packets'] for value in samples.values()])
        # out_packets = sum([value['out_packets'] for value in samples.values()])
        #
        # packet_drop = abs(out_packets - in_packets)
        # drop_percent = 100.0
        # try:
        #     drop_percent = round((packet_drop / float(out_packets)) * 100, 5)
        # except ZeroDivisionError:
        #     LOGGING.info('No traffic is flowing')
        #
        # # TODO(esm): RFC2544 doesn't tolerate packet loss, why do we?
        # tolerance_low = generator.rfc2544_helper.tolerance_low
        # tolerance_high = generator.rfc2544_helper.tolerance_high
        #
        # tx_rate = out_packets / run_duration
        # rx_rate = in_packets / run_duration
        #
        # throughput_max = self.throughput_max
        # drop_percent_at_max_tx = self.drop_percent_at_max_tx
        #
        # if self.drop_percent_at_max_tx is None:
        #     self.rate = tx_rate
        #     self.first_run = False
        #
        # if drop_percent > tolerance_high:
        #     # TODO(esm): why don't we discard results that are out of tolerance?
        #     self.max_rate = self.rate
        #     if throughput_max == 0:
        #         throughput_max = rx_rate
        #         drop_percent_at_max_tx = drop_percent
        #
        # elif drop_percent >= tolerance_low:
        #     # TODO(esm): why do we update the samples dict in this case
        #     #            and not update our tracking values?
        #     throughput_max = rx_rate
        #     drop_percent_at_max_tx = drop_percent
        #
        # elif drop_percent >= self.drop_percent_at_max_tx:
        #     # TODO(esm): why don't we discard results that are out of tolerance?
        #     self.min_rate = self.rate
        #     self.drop_percent_at_max_tx = drop_percent_at_max_tx = drop_percent
        #     self.throughput_max = throughput_max = rx_rate
        #
        # else:
        #     # TODO(esm): why don't we discard results that are out of tolerance?
        #     self.min_rate = self.rate
        #
        # generator.clear_client_stats(self.ports)
        # generator.start_client(self.ports, mult=self.get_multiplier(),
        #                        duration=run_duration, force=True)
        #
        # # if correlated traffic update the Throughput
        # if generator.rfc2544_helper.correlated_traffic:
        #     throughput_max *= 2
        #
        # samples.update({
        #     'TxThroughput': tx_rate,
        #     'RxThroughput': rx_rate,
        #     'CurrentDropPercentage': drop_percent,
        #     'Throughput': throughput_max,
        #     'DropPercentage': drop_percent_at_max_tx,
        # })

        return samples



    def start_client(self, ports, mult=None, duration=None, force=True):
        self.client.start(ports=ports, mult=mult, duration=duration, force=force)

    def clear_client_stats(self, ports):
        self.client.clear_stats(ports=ports)

    # def collect_kpi(self):
    #     self.rfc2544_helper.iteration.value += 1
    #     return super(TrexRfcResourceHelper, self).collect_kpi()


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
