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

from yardstick.network_services.traffic_profile.base import TrafficProfile
from trex_stl_lib.trex_stl_streams import STLTXCont
from trex_stl_lib.trex_stl_client import STLStream
from trex_stl_lib.trex_stl_packet_builder_scapy import STLPktBuilder
from trex_stl_lib import api as Pkt


class FixedProfile(TrafficProfile):
    """
    This profile adds a single stream at the beginning of the traffic session
    """
    def __init__(self, tp_config):
        super(FixedProfile, self).__init__(tp_config)
        self.first_run = True

    def execute(self, traffic_generator):
        if self.first_run:
            for index, ports in enumerate(traffic_generator.my_ports):
                ext_intf = \
                    traffic_generator.vnfd["vdu"][0]["external-interface"]
                virtual_interface = ext_intf[index]["virtual-interface"]
                src_ip = virtual_interface["local_ip"]
                dst_ip = virtual_interface["dst_ip"]

                traffic_generator.client.add_streams(
                    self._create_stream(src_ip, dst_ip),
                    ports=[ports])

            traffic_generator.client.start(ports=traffic_generator.my_ports,
                                           force=True)
            self.first_run = False

    def _create_stream(self, src_ip, dst_ip):
        base_frame = \
            Pkt.Ether() / Pkt.IP(src=src_ip, dst=dst_ip) / Pkt.UDP(dport=12,
                                                                   sport=1025)

        frame_size = self.params["traffic_profile"]["frame_size"]
        pad_size = max(0, frame_size - len(base_frame))
        frame = base_frame / ("x" * max(0, pad_size))

        frame_rate = self.params["traffic_profile"]["frame_rate"]
        return STLStream(packet=STLPktBuilder(pkt=frame),
                         mode=STLTXCont(pps=frame_rate))
