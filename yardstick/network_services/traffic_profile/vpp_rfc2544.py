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

import datetime
import ipaddress
import logging
import random
import string

from trex_stl_lib import api as Pkt
from trex_stl_lib import trex_stl_client
from trex_stl_lib import trex_stl_packet_builder_scapy
from trex_stl_lib import trex_stl_streams

from yardstick.common import constants
from yardstick.network_services.helpers.vpp_helpers.multiple_loss_ratio_search import \
    MultipleLossRatioSearch
from yardstick.network_services.traffic_profile.rfc2544 import RFC2544Profile, \
    PortPgIDMap
from yardstick.network_services.traffic_profile.trex_traffic_profile import IP, \
    DST

LOGGING = logging.getLogger(__name__)


class VppRFC2544Profile(RFC2544Profile):

    def __init__(self, traffic_generator):
        super(VppRFC2544Profile, self).__init__(traffic_generator)

        tp_cfg = traffic_generator["traffic_profile"]
        self.number_of_intermediate_phases = tp_cfg.get("intermediate_phases",
                                                        2)

        self.duration = self.config.duration
        self.precision = self.config.test_precision
        self.lower_bound = self.config.lower_bound
        self.upper_bound = self.config.upper_bound
        self.step_interval = self.config.step_interval
        self.enable_latency = self.config.enable_latency

        self.pkt_size = None
        self.flow = None

        self.tolerance_low = 0
        self.tolerance_high = 0

        self.queue = None
        self.port_pg_id = None

        self.current_lower = self.lower_bound
        self.current_upper = self.upper_bound

        self.ports = []
        self.profiles = {}

    @property
    def delta(self):
        return self.current_upper - self.current_lower

    @property
    def mid_point(self):
        return (self.current_lower + self.current_upper) / 2

    @staticmethod
    def calculate_frame_size(imix):
        if not imix:
            return 64, 100

        imix_count = {size.upper().replace('B', ''): int(weight)
                      for size, weight in imix.items()}
        imix_sum = sum(imix_count.values())
        if imix_sum <= 0:
            return 64, 100
        packets_total = sum([int(size) * weight
                             for size, weight in imix_count.items()])
        return packets_total / imix_sum, imix_sum

    @staticmethod
    def _gen_payload(length):
        payload = ""
        for _ in range(length):
            payload += random.choice(string.ascii_letters)

        return payload

    def bounds_iterator(self, logger=None):
        self.current_lower = self.lower_bound
        self.current_upper = self.upper_bound

        test_value = self.current_upper
        while abs(self.delta) >= self.precision:
            if logger:
                logger.debug("New interval [%s, %s), precision: %d",
                             self.current_lower,
                             self.current_upper, self.step_interval)
                logger.info("Testing with value %s", test_value)

            yield test_value
            test_value = self.mid_point

    def register_generator(self, generator):
        super(VppRFC2544Profile, self).register_generator(generator)
        self.init_traffic_params(generator)

    def init_queue(self, queue):
        self.queue = queue
        self.queue.cancel_join_thread()

    def init_traffic_params(self, generator):
        if generator.rfc2544_helper.latency:
            self.enable_latency = True
        self.tolerance_low = generator.rfc2544_helper.tolerance_low
        self.tolerance_high = generator.rfc2544_helper.tolerance_high
        self.max_rate = generator.scenario_helper.all_options.get('vpp_config',
                                                                  {}).get(
            'max_rate', self.rate)

    def create_profile(self, profile_data, current_port):
        streams = []
        for packet_name in profile_data:
            imix = (profile_data[packet_name].
                    get('outer_l2', {}).get('framesize'))
            self.pkt_size, imix_sum = self.calculate_frame_size(imix)
            self._create_vm(profile_data[packet_name])
            if self.max_rate > 100:
                imix_data = self._create_imix_data(imix,
                                                   constants.DISTRIBUTION_IN_PACKETS)
            else:
                imix_data = self._create_imix_data(imix)
            _streams = self._create_single_stream(current_port, imix_data,
                                                  imix_sum)
            streams.extend(_streams)
        return trex_stl_streams.STLProfile(streams)

    def _set_outer_l3v4_fields(self, outer_l3v4):
        """ setup outer l3v4 fields from traffic profile """
        ip_params = {}
        if 'proto' in outer_l3v4:
            ip_params['proto'] = outer_l3v4['proto']
        self._set_proto_fields(IP, **ip_params)

        self.flow = int(outer_l3v4['count'])
        src_start_ip, _ = outer_l3v4['srcip4'].split('-')
        dst_start_ip, _ = outer_l3v4['dstip4'].split('-')

        self.ip_packet = Pkt.IP(src=src_start_ip,
                                dst=dst_start_ip,
                                proto=outer_l3v4['proto'])
        if self.flow > 1:
            dst_start_int = int(ipaddress.ip_address(str(dst_start_ip)))
            dst_end_ip_new = ipaddress.ip_address(
                dst_start_int + self.flow - 1)
            # self._set_proto_addr(IP, SRC, outer_l3v4['srcip4'], outer_l3v4['count'])
            self._set_proto_addr(IP, DST,
                                 "{start_ip}-{end_ip}".format(
                                     start_ip=dst_start_ip,
                                     end_ip=str(dst_end_ip_new)),
                                 self.flow)

    def _create_single_packet(self, size=64):
        ether_packet = self.ether_packet
        ip_packet = self.ip6_packet if self.ip6_packet else self.ip_packet
        base_pkt = ether_packet / ip_packet
        payload_len = max(0, size - len(base_pkt) - 4)
        packet = trex_stl_packet_builder_scapy.STLPktBuilder(
            pkt=base_pkt / self._gen_payload(payload_len),
            vm=self.trex_vm)
        packet_lat = trex_stl_packet_builder_scapy.STLPktBuilder(
            pkt=base_pkt / self._gen_payload(payload_len))

        return packet, packet_lat

    def _create_single_stream(self, current_port, imix_data, imix_sum,
                              isg=0.0):
        streams = []
        for size, weight in ((int(size), float(weight)) for (size, weight)
                             in imix_data.items() if float(weight) > 0):
            if current_port == 1:
                isg += 10.0
            if self.max_rate > 100:
                mode = trex_stl_streams.STLTXCont(
                    pps=int(weight * imix_sum / 100))
                mode_lat = mode
            else:
                mode = trex_stl_streams.STLTXCont(
                    percentage=weight * self.max_rate / 100)
                mode_lat = trex_stl_streams.STLTXCont(pps=9000)

            packet, packet_lat = self._create_single_packet(size)
            streams.append(
                trex_stl_client.STLStream(isg=isg, packet=packet, mode=mode))
            if self.enable_latency:
                pg_id = self.port_pg_id.increase_pg_id(current_port)
                stl_flow = trex_stl_streams.STLFlowLatencyStats(pg_id=pg_id)
                stream_lat = trex_stl_client.STLStream(isg=isg,
                                                       packet=packet_lat,
                                                       mode=mode_lat,
                                                       flow_stats=stl_flow)
                streams.append(stream_lat)
        return streams

    def execute_traffic(self, traffic_generator=None):
        if traffic_generator is not None and self.generator is None:
            self.generator = traffic_generator

        self.ports = []
        self.profiles = {}
        self.port_pg_id = PortPgIDMap()
        for vld_id, intfs in sorted(self.generator.networks.items()):
            profile_data = self.params.get(vld_id)
            if not profile_data:
                continue
            if (vld_id.startswith(self.DOWNLINK) and
                    self.generator.rfc2544_helper.correlated_traffic):
                continue
            for intf in intfs:
                current_port = int(self.generator.port_num(intf))
                self.port_pg_id.add_port(current_port)
                profile = self.create_profile(profile_data, current_port)
                self.generator.client.add_streams(profile,
                                                  ports=[current_port])

                self.ports.append(current_port)
                self.profiles[current_port] = profile

        timeout = self.generator.scenario_helper.scenario_cfg["runner"][
            "duration"]
        test_data = {
            "test_duration": timeout,
            "test_precision": self.precision,
            "tolerated_loss": self.tolerance_high,
            "duration": self.duration,
            "packet_size": self.pkt_size,
            "flow": self.flow
        }

        if self.max_rate > 100:
            self.binary_search_with_optimized(self.generator, self.duration,
                                              timeout, test_data)
        else:
            self.binary_search(self.generator, self.duration,
                               self.tolerance_high, test_data)

    def binary_search_with_optimized(self, traffic_generator, duration,
                                     timeout, test_data):
        self.queue.cancel_join_thread()
        algorithm = MultipleLossRatioSearch(
            measurer=traffic_generator, latency=self.enable_latency,
            pkt_size=self.pkt_size,
            final_trial_duration=duration,
            final_relative_width=self.step_interval / 100,
            number_of_intermediate_phases=self.number_of_intermediate_phases,
            initial_trial_duration=1,
            timeout=timeout)
        algorithm.init_generator(self.ports, self.port_pg_id, self.profiles,
                                 test_data, self.queue)
        return algorithm.narrow_down_ndr_and_pdr(10000, self.max_rate,
                                                 self.tolerance_high)

    def binary_search(self, traffic_generator, duration, tolerance_value,
                      test_data):
        theor_max_thruput = 0
        result_samples = {}

        for test_value in self.bounds_iterator(LOGGING):
            stats = traffic_generator.send_traffic_on_tg(self.ports,
                                                         self.port_pg_id,
                                                         duration,
                                                         str(
                                                             test_value / self.max_rate / 2),
                                                         latency=self.enable_latency)
            traffic_generator.client.reset(ports=self.ports)
            traffic_generator.client.clear_stats(ports=self.ports)
            traffic_generator.client.remove_all_streams(ports=self.ports)
            for port, profile in self.profiles.items():
                traffic_generator.client.add_streams(profile, ports=[port])

            loss_ratio = (float(traffic_generator.loss) / float(
                traffic_generator.sent)) * 100

            samples = traffic_generator.generate_samples(stats, self.ports,
                                                         self.port_pg_id,
                                                         self.enable_latency)
            samples.update(test_data)
            LOGGING.info("Collect TG KPIs %s %s %s", datetime.datetime.now(),
                         test_value, samples)
            self.queue.put(samples)

            if float(loss_ratio) > float(tolerance_value):
                LOGGING.debug("Failure... Decreasing upper bound")
                self.current_upper = test_value
            else:
                LOGGING.debug("Success! Increasing lower bound")
                self.current_lower = test_value

                rate_total = float(traffic_generator.sent) / float(duration)
                bandwidth_total = float(rate_total) * (
                        float(self.pkt_size) + 20) * 8 / (10 ** 9)

                success_samples = {'Result_' + key: value for key, value in
                                   samples.items()}
                success_samples["Result_{}".format('PDR')] = {
                    "rate_total_pps": float(rate_total),
                    "bandwidth_total_Gbps": float(bandwidth_total),
                    "packet_loss_ratio": float(loss_ratio),
                    "packets_lost": int(traffic_generator.loss),
                }
                self.queue.put(success_samples)

                # Store Actual throughput for result samples
                for intf in traffic_generator.vnfd_helper.interfaces:
                    name = intf["name"]
                    result_samples[name] = {
                        "Result_Actual_throughput": float(
                            success_samples["Result_{}".format(name)][
                                "rx_throughput_bps"]),
                    }

            for intf in traffic_generator.vnfd_helper.interfaces:
                name = intf["name"]
                if theor_max_thruput < samples[name]["tx_throughput_bps"]:
                    theor_max_thruput = samples[name]['tx_throughput_bps']
                    self.queue.put({'theor_max_throughput': theor_max_thruput})

        result_samples["Result_theor_max_throughput"] = theor_max_thruput
        self.queue.put(result_samples)
        return result_samples
