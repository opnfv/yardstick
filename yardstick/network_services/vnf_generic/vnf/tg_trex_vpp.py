# Copyright (c) 2019 Viosoft Corporation
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

from trex_stl_lib.trex_stl_exceptions import STLError

from yardstick.common.utils import safe_cast
from yardstick.network_services.vnf_generic.vnf.sample_vnf import \
    Rfc2544ResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import \
    SampleVNFTrafficGen
from yardstick.network_services.vnf_generic.vnf.tg_trex import \
    TrexDpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.tg_trex import \
    TrexResourceHelper

LOGGING = logging.getLogger(__name__)


class TrexVppResourceHelper(TrexResourceHelper):

    def __init__(self, setup_helper, rfc_helper_type=None):
        super(TrexVppResourceHelper, self).__init__(setup_helper)

        if rfc_helper_type is None:
            rfc_helper_type = Rfc2544ResourceHelper

        self.rfc2544_helper = rfc_helper_type(self.scenario_helper)

        self.loss = None
        self.sent = None
        self.latency = None

    def generate_samples(self, stats=None, ports=None, port_pg_id=None,
                         latency=False):
        samples = {}
        if stats is None:
            stats = self.get_stats(ports)
        for pname in (intf['name'] for intf in self.vnfd_helper.interfaces):
            port_num = self.vnfd_helper.port_num(pname)
            port_stats = stats.get(port_num, {})
            samples[pname] = {
                'rx_throughput_fps': float(port_stats.get('rx_pps', 0.0)),
                'tx_throughput_fps': float(port_stats.get('tx_pps', 0.0)),
                'rx_throughput_bps': float(port_stats.get('rx_bps', 0.0)),
                'tx_throughput_bps': float(port_stats.get('tx_bps', 0.0)),
                'in_packets': int(port_stats.get('ipackets', 0)),
                'out_packets': int(port_stats.get('opackets', 0)),
            }

            if latency:
                pg_id_list = port_pg_id.get_pg_ids(port_num)
                samples[pname]['latency'] = {}
                for pg_id in pg_id_list:
                    latency_global = stats.get('latency', {})
                    pg_latency = latency_global.get(pg_id, {}).get('latency')

                    t_min = safe_cast(pg_latency.get("total_min", 0.0), float,
                                      -1.0)
                    t_avg = safe_cast(pg_latency.get("average", 0.0), float,
                                      -1.0)
                    t_max = safe_cast(pg_latency.get("total_max", 0.0), float,
                                      -1.0)

                    latency = {
                        "min_latency": t_min,
                        "max_latency": t_max,
                        "avg_latency": t_avg,
                    }
                    samples[pname]['latency'][pg_id] = latency

        return samples

    def _run_traffic_once(self, traffic_profile):
        self.client_started.value = 1
        traffic_profile.execute_traffic(self)
        return True

    def run_traffic(self, traffic_profile):
        self._queue.cancel_join_thread()
        traffic_profile.init_queue(self._queue)
        super(TrexVppResourceHelper, self).run_traffic(traffic_profile)

    @staticmethod
    def fmt_latency(lat_min, lat_avg, lat_max):
        t_min = int(round(safe_cast(lat_min, float, -1.0)))
        t_avg = int(round(safe_cast(lat_avg, float, -1.0)))
        t_max = int(round(safe_cast(lat_max, float, -1.0)))

        return "/".join(str(tmp) for tmp in (t_min, t_avg, t_max))

    def send_traffic_on_tg(self, ports, port_pg_id, duration, rate,
                           latency=False):
        try:
            # Choose rate and start traffic:
            self.client.start(ports=ports, mult=rate, duration=duration)
            # Block until done:
            try:
                self.client.wait_on_traffic(ports=ports, timeout=duration + 20)
            except STLError as err:
                self.client.stop(ports)
                LOGGING.error("TRex stateless timeout error: %s", err)

            if self.client.get_warnings():
                for warning in self.client.get_warnings():
                    LOGGING.warning(warning)

            # Read the stats after the test
            stats = self.client.get_stats()

            packets_in = []
            packets_out = []
            for port in ports:
                packets_in.append(stats[port]["ipackets"])
                packets_out.append(stats[port]["opackets"])

                if latency:
                    self.latency = []
                    pg_id_list = port_pg_id.get_pg_ids(port)
                    for pg_id in pg_id_list:
                        latency_global = stats.get('latency', {})
                        pg_latency = latency_global.get(pg_id, {}).get(
                            'latency')
                        lat = self.fmt_latency(
                            str(pg_latency.get("total_min")),
                            str(pg_latency.get("average")),
                            str(pg_latency.get("total_max")))
                        LOGGING.info(
                            "latencyStream%s(usec)=%s", pg_id, lat)
                        self.latency.append(lat)

            self.sent = sum(packets_out)
            total_rcvd = sum(packets_in)
            self.loss = self.sent - total_rcvd
            LOGGING.info("rate=%s, totalReceived=%s, totalSent=%s,"
                         " frameLoss=%s", rate, total_rcvd, self.sent,
                         self.loss)
            return stats
        except STLError as err:
            LOGGING.error("TRex stateless runtime error: %s", err)
            raise RuntimeError('TRex stateless runtime error')


class TrexTrafficGenVpp(SampleVNFTrafficGen):
    APP_NAME = 'TRex'
    WAIT_TIME = 20

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = TrexDpdkVnfSetupEnvHelper
        if resource_helper_type is None:
            resource_helper_type = TrexVppResourceHelper

        super(TrexTrafficGenVpp, self).__init__(
            name, vnfd, setup_env_helper_type, resource_helper_type)

    def _check_status(self):
        return self.resource_helper.check_status()

    def _start_server(self):
        super(TrexTrafficGenVpp, self)._start_server()
        self.resource_helper.start()

    def wait_for_instantiate(self):
        return self._wait_for_process()
