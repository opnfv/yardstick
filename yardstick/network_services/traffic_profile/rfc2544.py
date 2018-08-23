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

import logging

from trex_stl_lib import api as Pkt
from trex_stl_lib import trex_stl_client
from trex_stl_lib import trex_stl_packet_builder_scapy
from trex_stl_lib import trex_stl_streams

from yardstick.common import constants
from yardstick.network_services.traffic_profile import trex_traffic_profile


LOGGING = logging.getLogger(__name__)
SRC_PORT = 'sport'
DST_PORT = 'dport'


class PortPgIDMap(object):
    """Port and pg_id mapping class

    "pg_id" is the identification STL library gives to each stream. In the
    RFC2544Profile class, the traffic has a STLProfile per port, which contains
    one or several streams, one per packet size defined in the IMIX test case
    description.

    Example of port <-> pg_id map:
        self._port_pg_id_map = {
            0: [1, 2, 3, 4],
            1: [5, 6, 7, 8]
        }
    """

    def __init__(self):
        self._pg_id = 0
        self._last_port = None
        self._port_pg_id_map = {}

    def add_port(self, port):
        self._last_port = port
        self._port_pg_id_map[port] = []

    def get_pg_ids(self, port):
        return self._port_pg_id_map.get(port, [])

    def increase_pg_id(self, port=None):
        port = self._last_port if not port else port
        if port is None:
            return
        pg_id_list = self._port_pg_id_map.get(port)
        if not pg_id_list:
            self.add_port(port)
            pg_id_list = self._port_pg_id_map[port]
        self._pg_id += 1
        pg_id_list.append(self._pg_id)
        return self._pg_id


class RFC2544Profile(trex_traffic_profile.TrexProfile):
    """TRex RFC2544 traffic profile"""

    TOLERANCE_LIMIT = 0.01

    def __init__(self, traffic_generator):
        super(RFC2544Profile, self).__init__(traffic_generator)
        self.generator = None
        self.rate = self.config.frame_rate
        self.max_rate = self.config.frame_rate
        self.min_rate = 0
        self.drop_percent_max = 0

    def register_generator(self, generator):
        self.generator = generator

    def stop_traffic(self, traffic_generator=None):
        """"Stop traffic injection, reset counters and remove streams"""
        if traffic_generator is not None and self.generator is None:
            self.generator = traffic_generator

        self.generator.client.stop()
        self.generator.client.reset()
        self.generator.client.remove_all_streams()

    def execute_traffic(self, traffic_generator=None):
        """Generate the stream and run traffic on the given ports

        :param traffic_generator: (TrexTrafficGenRFC) traffic generator
        :return ports: (list of int) indexes of ports
                port_pg_id: (dict) port indexes and pg_id [1] map
        [1] https://trex-tgn.cisco.com/trex/doc/cp_stl_docs/api/
            profile_code.html#stlstream-modes
        """
        if traffic_generator is not None and self.generator is None:
            self.generator = traffic_generator

        port_pg_id = PortPgIDMap()
        ports = []
        for vld_id, intfs in sorted(self.generator.networks.items()):
            profile_data = self.params.get(vld_id)
            if not profile_data:
                continue
            if (vld_id.startswith(self.DOWNLINK) and
                    self.generator.rfc2544_helper.correlated_traffic):
                continue
            for intf in intfs:
                port_num = int(self.generator.port_num(intf))
                ports.append(port_num)
                port_pg_id.add_port(port_num)
                profile = self._create_profile(profile_data,
                                               self.rate, port_pg_id,
                                               self.config.enable_latency)
                self.generator.client.add_streams(profile, ports=[port_num])

        self.generator.client.start(ports=ports,
                                    duration=self.config.duration,
                                    force=True)
        return ports, port_pg_id

    def _create_profile(self, profile_data, rate, port_pg_id, enable_latency):
        """Create a STL profile (list of streams) for a port"""
        streams = []
        for packet_name in profile_data:
            imix = (profile_data[packet_name].
                    get('outer_l2', {}).get('framesize'))
            imix_data = self._create_imix_data(imix)
            self._create_vm(profile_data[packet_name])
            _streams = self._create_streams(imix_data, rate, port_pg_id,
                                            enable_latency)
            streams.extend(_streams)
        return trex_stl_streams.STLProfile(streams)

    def _create_imix_data(self, imix,
                          weight_mode=constants.DISTRIBUTION_IN_PACKETS):
        """Generate the IMIX distribution for a STL profile

        The input information is the framesize dictionary in a test case
        traffic profile definition. E.g.:
          downlink_0:
            ipv4:
              id: 2
                outer_l2:
                  framesize:
                    64B: 10
                    128B: 20
                    ...

        This function normalizes the sum of framesize weights to 100 and
        returns a dictionary of frame sizes in bytes and weight in percentage.
        E.g.:
          imix_count = {64: 25, 128: 75}

        The weight mode is described in [1]. There are two ways to describe the
        weight of the packets:
          - Distribution in packets: the weight defines the percentage of
            packets sent per packet size. IXIA uses this definition.
          - Distribution in bytes: the weight defines the percentage of bytes
            sent per packet size.

        Packet size  # packets  D. in packets  Bytes  D. in bytes
        40           7          58.33%         280    7%
        576          4          33.33%         2304   56%
        1500         1          8.33%          1500   37%

        [1] https://en.wikipedia.org/wiki/Internet_Mix

        :param imix: (dict) IMIX size and weight
        """
        imix_count = {}
        if not imix:
            return imix_count

        imix_count = {size.upper().replace('B', ''): int(weight)
                      for size, weight in imix.items()}
        imix_sum = sum(imix_count.values())
        if imix_sum <= 0:
            imix_count = {64: 100}
            imix_sum = 100

        weight_normalize = float(imix_sum) / 100
        imix_dip = {size: float(weight) / weight_normalize
                    for size, weight in imix_count.items()}

        if weight_mode == constants.DISTRIBUTION_IN_BYTES:
            return imix_dip

        byte_total = sum([int(size) * weight
                          for size, weight in imix_dip.items()])
        return {size: (int(size) * weight) / byte_total
                for size, weight in imix_dip.items()}

    def _create_vm(self, packet_definition):
        """Create the STL Raw instructions"""
        self.ether_packet = Pkt.Ether()
        self.ip_packet = Pkt.IP()
        self.ip6_packet = None
        self.udp_packet = Pkt.UDP()
        self.udp[DST_PORT] = 'UDP.dport'
        self.udp[SRC_PORT] = 'UDP.sport'
        self.qinq = False
        self.vm_flow_vars = []
        outer_l2 = packet_definition.get('outer_l2')
        outer_l3v4 = packet_definition.get('outer_l3v4')
        outer_l3v6 = packet_definition.get('outer_l3v6')
        outer_l4 = packet_definition.get('outer_l4')
        if outer_l2:
            self._set_outer_l2_fields(outer_l2)
        if outer_l3v4:
            self._set_outer_l3v4_fields(outer_l3v4)
        if outer_l3v6:
            self._set_outer_l3v6_fields(outer_l3v6)
        if outer_l4:
            self._set_outer_l4_fields(outer_l4)
        self.trex_vm = trex_stl_packet_builder_scapy.STLScVmRaw(
            self.vm_flow_vars)

    def _create_single_packet(self, size=64):
        size -= 4
        ether_packet = self.ether_packet
        ip_packet = self.ip6_packet if self.ip6_packet else self.ip_packet
        udp_packet = self.udp_packet
        if self.qinq:
            qinq_packet = self.qinq_packet
            base_pkt = ether_packet / qinq_packet / ip_packet / udp_packet
        else:
            base_pkt = ether_packet / ip_packet / udp_packet
        pad = max(0, size - len(base_pkt)) * 'x'
        return trex_stl_packet_builder_scapy.STLPktBuilder(
            pkt=base_pkt / pad, vm=self.trex_vm)

    def _create_streams(self, imix_data, rate, port_pg_id, enable_latency):
        """Create a list of streams per packet size

        The STL TX mode speed of the generated streams will depend on the frame
        weight and the frame rate. Both the frame weight and the total frame
        rate are normalized to 100. The STL TX mode speed, defined in
        percentage, is the combitation of both percentages. E.g.:
          frame weight = 100
          rate = 90
            --> STLTXmode percentage = 10 (%)

          frame weight = 80
          rate = 50
            --> STLTXmode percentage = 40 (%)

        :param imix_data: (dict) IMIX size and weight
        :param rate: (float) normalized [0..100] total weight
        :param pg_id: (PortPgIDMap) port / pg_id (list) map
        """
        streams = []
        for size, weight in ((int(size), float(weight)) for (size, weight)
                             in imix_data.items() if float(weight) > 0):
            packet = self._create_single_packet(size)
            pg_id = port_pg_id.increase_pg_id()
            stl_flow = (trex_stl_streams.STLFlowLatencyStats(pg_id=pg_id) if
                        enable_latency else None)
            mode = trex_stl_streams.STLTXCont(percentage=weight * rate / 100)
            streams.append(trex_stl_client.STLStream(
                packet=packet, flow_stats=stl_flow, mode=mode))
        return streams

    def get_drop_percentage(self, samples, tol_low, tol_high,
                            correlated_traffic):
        """Calculate the drop percentage and run the traffic"""
        completed = False
        out_pkt_end = sum(port['out_packets'] for port in samples[-1].values())
        in_pkt_end = sum(port['in_packets'] for port in samples[-1].values())
        out_pkt_ini = sum(port['out_packets'] for port in samples[0].values())
        in_pkt_ini = sum(port['in_packets'] for port in samples[0].values())
        time_diff = (list(samples[-1].values())[0]['timestamp'] -
                     list(samples[0].values())[0]['timestamp']).total_seconds()
        out_packets = out_pkt_end - out_pkt_ini
        in_packets = in_pkt_end - in_pkt_ini
        tx_rate_fps = float(out_packets) / time_diff
        rx_rate_fps = float(in_packets) / time_diff
        drop_percent = 100.0

        # https://tools.ietf.org/html/rfc2544#section-26.3
        if out_packets:
            drop_percent = round(
                (float(abs(out_packets - in_packets)) / out_packets) * 100, 5)

        tol_high = max(tol_high, self.TOLERANCE_LIMIT)
        tol_low = min(tol_low, self.TOLERANCE_LIMIT)
        if drop_percent > tol_high:
            self.max_rate = self.rate
        elif drop_percent < tol_low:
            self.min_rate = self.rate
        else:
            completed = True

        last_rate = self.rate
        self.rate = round(float(self.max_rate + self.min_rate) / 2.0, 5)

        throughput = rx_rate_fps * 2 if correlated_traffic else rx_rate_fps

        if drop_percent > self.drop_percent_max:
            self.drop_percent_max = drop_percent

        latency = {port_num: value['latency']
                   for port_num, value in samples[-1].items()}

        output = {
            'TxThroughput': tx_rate_fps,
            'RxThroughput': rx_rate_fps,
            'CurrentDropPercentage': drop_percent,
            'Throughput': throughput,
            'DropPercentage': self.drop_percent_max,
            'Rate': last_rate,
            'Latency': latency
        }
        return completed, output
