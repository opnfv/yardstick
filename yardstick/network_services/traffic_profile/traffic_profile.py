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
""" Trex Traffic Profile definitions """

from __future__ import absolute_import
import struct
import socket
import logging
from random import SystemRandom
import six

from yardstick.network_services.traffic_profile.base import TrafficProfile
from trex_stl_lib.trex_stl_client import STLStream
from trex_stl_lib.trex_stl_streams import STLFlowLatencyStats
from trex_stl_lib.trex_stl_streams import STLTXCont
from trex_stl_lib.trex_stl_streams import STLProfile
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmWrFlowVar
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmFlowVarRepeatableRandom
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmFlowVar
from trex_stl_lib.trex_stl_packet_builder_scapy import STLPktBuilder
from trex_stl_lib.trex_stl_packet_builder_scapy import STLScVmRaw
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmFixIpv4
from trex_stl_lib import api as Pkt


class TrexProfile(TrafficProfile):
    """ This class handles Trex Traffic profile generation and execution """

    def __init__(self, yaml_data):
        super(TrexProfile, self).__init__(yaml_data)
        self.flows = 100
        self.pps = 100
        self.pg_id = 0
        self.first_run = True
        self.streams = 1
        self.profile_data = []
        self.profile = None
        self.base_pkt = None
        self.fsize = None
        self.trex_vm = None
        self.vms = []
        self.rate = None
        self.ip_packet = None
        self.ip6_packet = None
        self.udp_packet = None
        self.udp_dport = ''
        self.udp_sport = ''
        self.qinq_packet = None
        self.qinq = False
        self.vm_flow_vars = []
        self.packets = []
        self.ether_packet = []

    def execute(self, traffic_generator):
        """ Generate the stream and run traffic on the given ports """
        pass

    def _set_ether_fields(self, **kwargs):
        """ set ethernet protocol fields """
        if not self.ether_packet:
            self.ether_packet = Pkt.Ether()
            for key, value in six.iteritems(kwargs):
                setattr(self.ether_packet, key, value)

    def _set_ip_fields(self, **kwargs):
        """ set l3 ipv4 protocol fields """

        if not self.ip_packet:
            self.ip_packet = Pkt.IP()
        for key in kwargs:
            setattr(self.ip_packet, key, kwargs[key])

    def _set_ip6_fields(self, **kwargs):
        """ set l3 ipv6 protocol fields """
        if not self.ip6_packet:
            self.ip6_packet = Pkt.IPv6()
        for key in kwargs:
            setattr(self.ip6_packet, key, kwargs[key])

    def _set_udp_fields(self, **kwargs):
        """ set l4 udp ports fields """
        if not self.udp_packet:
            self.udp_packet = Pkt.UDP()
        for key in kwargs:
            setattr(self.udp_packet, key, kwargs[key])

    def set_src_mac(self, src_mac):
        """ set source mac address fields """
        src_macs = src_mac.split('-')
        min_value = src_macs[0]
        if len(src_macs) == 1:
            src_mac = min_value
            self._set_ether_fields(src=src_mac)
        else:
            stl_vm_flow_var = STLVmFlowVar(name="mac_src",
                                           min_value=1,
                                           max_value=30,
                                           size=4,
                                           op='inc',
                                           step=1)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='mac_src',
                                                pkt_offset='Ether.src')
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_dst_mac(self, dst_mac):
        """ set destination mac address fields """
        dst_macs = dst_mac.split('-')
        min_value = dst_macs[0]
        if len(dst_macs) == 1:
            dst_mac = min_value
            self._set_ether_fields(dst=dst_mac)
        else:
            stl_vm_flow_var = STLVmFlowVar(name="mac_dst",
                                           min_value=1,
                                           max_value=30,
                                           size=4,
                                           op='inc',
                                           step=1)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='mac_dst',
                                                pkt_offset='Ether.dst')
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_src_ip4(self, src_ip4, count=1):
        """ set source ipv4 address fields """
        src_ips = src_ip4.split('-')
        min_value = src_ips[0]
        max_value = src_ips[1] if len(src_ips) == 2 else src_ips[0]
        if len(src_ips) == 1:
            src_ip4 = min_value
            self._set_ip_fields(src=src_ip4)
        else:
            stl_vm_flow_var = STLVmFlowVarRepeatableRandom(name="ip4_src",
                                                           min_value=min_value,
                                                           max_value=max_value,
                                                           size=4,
                                                           limit=int(count),
                                                           seed=0x1235)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='ip4_src',
                                                pkt_offset='IP.src')
            self.vm_flow_vars.append(stl_vm_wr_flow_var)
            stl_vm_fix_ipv4 = STLVmFixIpv4(offset="IP")
            self.vm_flow_vars.append(stl_vm_fix_ipv4)

    def set_dst_ip4(self, dst_ip4, count=1):
        """ set destination ipv4 address fields """
        dst_ips = dst_ip4.split('-')
        min_value = dst_ips[0]
        max_value = dst_ips[1] if len(dst_ips) == 2 else dst_ips[0]
        if len(dst_ips) == 1:
            dst_ip4 = min_value
            self._set_ip_fields(dst=dst_ip4)
        else:
            stl_vm_flow_var = STLVmFlowVarRepeatableRandom(name="dst_ip4",
                                                           min_value=min_value,
                                                           max_value=max_value,
                                                           size=4,
                                                           limit=int(count),
                                                           seed=0x1235)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='dst_ip4',
                                                pkt_offset='IP.dst')
            self.vm_flow_vars.append(stl_vm_wr_flow_var)
            stl_vm_fix_ipv4 = STLVmFixIpv4(offset="IP")
            self.vm_flow_vars.append(stl_vm_fix_ipv4)

    def set_src_ip6(self, src_ip6):
        """ set source ipv6 address fields """
        src_ips = src_ip6.split('-')
        min_value = src_ips[0]
        max_value = src_ips[1] if len(src_ips) == 2 else src_ips[0]
        src_ip6 = min_value
        self._set_ip6_fields(src=src_ip6)
        if len(src_ips) == 2:
            min_value, max_value = \
                self._get_start_end_ipv6(min_value, max_value)
            stl_vm_flow_var = STLVmFlowVar(name="ip6_src",
                                           min_value=min_value,
                                           max_value=max_value,
                                           size=8,
                                           op='random',
                                           step=1)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='ip6_src',
                                                pkt_offset='IPv6.src',
                                                offset_fixup=8)
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_dst_ip6(self, dst_ip6):
        """ set destination ipv6 address fields """
        dst_ips = dst_ip6.split('-')
        min_value = dst_ips[0]
        max_value = dst_ips[1] if len(dst_ips) == 2 else dst_ips[0]
        dst_ip6 = min_value
        self._set_ip6_fields(dst=dst_ip6)
        if len(dst_ips) == 2:
            min_value, max_value = \
                self._get_start_end_ipv6(min_value, max_value)
            stl_vm_flow_var = STLVmFlowVar(name="dst_ip6",
                                           min_value=min_value,
                                           max_value=max_value,
                                           size=8,
                                           op='random',
                                           step=1)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='dst_ip6',
                                                pkt_offset='IPv6.dst',
                                                offset_fixup=8)
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_dscp(self, dscp):
        """ set dscp for trex """
        dscps = str(dscp).split('-')
        min_value = int(dscps[0])
        max_value = int(dscps[1]) if len(dscps) == 2 else int(dscps[0])
        if len(dscps) == 1:
            dscp = min_value
            self._set_ip_fields(tos=dscp)
        else:
            stl_vm_flow_var = STLVmFlowVar(name="dscp",
                                           min_value=min_value,
                                           max_value=max_value,
                                           size=2,
                                           op='inc',
                                           step=8)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='dscp',
                                                pkt_offset='IP.tos')
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_src_port(self, src_port, count=1):
        """ set packet source port """
        src_ports = str(src_port).split('-')
        min_value = int(src_ports[0])
        if len(src_ports) == 1:
            max_value = int(src_ports[0])
            src_port = min_value
            self._set_udp_fields(sport=src_port)
        else:
            max_value = int(src_ports[1])
            stl_vm_flow_var = STLVmFlowVarRepeatableRandom(name="port_src",
                                                           min_value=min_value,
                                                           max_value=max_value,
                                                           size=2,
                                                           limit=int(count),
                                                           seed=0x1235)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='port_src',
                                                pkt_offset=self.udp_sport)
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_dst_port(self, dst_port, count=1):
        """ set packet destnation port """
        dst_ports = str(dst_port).split('-')
        min_value = int(dst_ports[0])
        if len(dst_ports) == 1:
            max_value = int(dst_ports[0])
            dst_port = min_value
            self._set_udp_fields(dport=dst_port)
        else:
            max_value = int(dst_ports[1])
            stl_vm_flow_var = \
                STLVmFlowVarRepeatableRandom(name="port_dst",
                                             min_value=min_value,
                                             max_value=max_value,
                                             size=2,
                                             limit=int(count),
                                             seed=0x1235)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(fv_name='port_dst',
                                                pkt_offset=self.udp_dport)
            self.vm_flow_vars.append(stl_vm_wr_flow_var)

    def set_svlan_cvlan(self, svlan, cvlan):
        """ set svlan & cvlan """
        self.qinq = True
        ether_params = {'type': 0x8100}
        self._set_ether_fields(**ether_params)
        svlans = str(svlan['id']).split('-')
        svlan_min = int(svlans[0])
        svlan_max = int(svlans[1]) if len(svlans) == 2 else int(svlans[0])
        if len(svlans) == 2:
            svlan = self._get_random_value(svlan_min, svlan_max)
        else:
            svlan = svlan_min
        cvlans = str(cvlan['id']).split('-')
        cvlan_min = int(cvlans[0])
        cvlan_max = int(cvlans[1]) if len(cvlans) == 2 else int(cvlans[0])
        if len(cvlans) == 2:
            cvlan = self._get_random_value(cvlan_min, cvlan_max)
        else:
            cvlan = cvlan_min
        self.qinq_packet = Pkt.Dot1Q(vlan=svlan) / Pkt.Dot1Q(vlan=cvlan)

    def set_qinq(self, qinq):
        """ set qinq in packet """
        self.set_svlan_cvlan(qinq['S-VLAN'], qinq['C-VLAN'])

    def set_outer_l2_fields(self, outer_l2):
        """ setup outer l2 fields from traffic profile """
        ether_params = {'type': 0x800}
        self._set_ether_fields(**ether_params)
        if 'srcmac' in outer_l2:
            self.set_src_mac(outer_l2['srcmac'])
        if 'dstmac' in outer_l2:
            self.set_dst_mac(outer_l2['dstmac'])
        if 'QinQ' in outer_l2:
            self.set_qinq(outer_l2['QinQ'])

    def set_outer_l3v4_fields(self, outer_l3v4):
        """ setup outer l3v4 fields from traffic profile """
        ip_params = {}
        if 'proto' in outer_l3v4:
            ip_params['proto'] = outer_l3v4['proto']
            if outer_l3v4['proto'] == 'tcp':
                self.udp_packet = Pkt.TCP()
                self.udp_dport = 'TCP.dport'
                self.udp_sport = 'TCP.sport'
                tcp_params = {'flags': '', 'window': 0}
                self._set_udp_fields(**tcp_params)
        if 'ttl' in outer_l3v4:
            ip_params['ttl'] = outer_l3v4['ttl']
        self._set_ip_fields(**ip_params)
        if 'dscp' in outer_l3v4:
            self.set_dscp(outer_l3v4['dscp'])
        if 'srcip4' in outer_l3v4:
            self.set_src_ip4(outer_l3v4['srcip4'], outer_l3v4['count'])
        if 'dstip4' in outer_l3v4:
            self.set_dst_ip4(outer_l3v4['dstip4'], outer_l3v4['count'])

    def set_outer_l3v6_fields(self, outer_l3v6):
        """ setup outer l3v6 fields from traffic profile """
        ether_params = {'type': 0x86dd}
        self._set_ether_fields(**ether_params)
        ip6_params = {}
        if 'proto' in outer_l3v6:
            ip6_params['proto'] = outer_l3v6['proto']
            if outer_l3v6['proto'] == 'tcp':
                self.udp_packet = Pkt.TCP()
                self.udp_dport = 'TCP.dport'
                self.udp_sport = 'TCP.sport'
                tcp_params = {'flags': '', 'window': 0}
                self._set_udp_fields(**tcp_params)
        if 'ttl' in outer_l3v6:
            ip6_params['ttl'] = outer_l3v6['ttl']
        if 'tc' in outer_l3v6:
            ip6_params['tc'] = outer_l3v6['tc']
        if 'hlim' in outer_l3v6:
            ip6_params['hlim'] = outer_l3v6['hlim']
        self._set_ip6_fields(**ip6_params)
        if 'srcip6' in outer_l3v6:
            self.set_src_ip6(outer_l3v6['srcip6'])
        if 'dstip6' in outer_l3v6:
            self.set_dst_ip6(outer_l3v6['dstip6'])

    def set_outer_l4_fields(self, outer_l4):
        """ setup outer l4 fields from traffic profile """
        if 'srcport' in outer_l4:
            self.set_src_port(outer_l4['srcport'], outer_l4['count'])
        if 'dstport' in outer_l4:
            self.set_dst_port(outer_l4['dstport'], outer_l4['count'])

    def generate_imix_data(self, packet_definition):
        """ generate packet size for a given traffic profile """
        imix_count = {}
        imix_data = {}
        if not packet_definition:
            return imix_count
        imix = packet_definition.get('framesize')
        if imix:
            for size in imix:
                data = imix[size]
                imix_data[int(size[:-1])] = int(data)
            imix_sum = sum(imix_data.values())
            if imix_sum > 100:
                raise SystemExit("Error in IMIX data")
            elif imix_sum < 100:
                imix_data[64] = imix_data.get(64, 0) + (100 - imix_sum)

            avg_size = 0.0
            for size in imix_data:
                count = int(imix_data[size])
                if count:
                    avg_size += round(size * count / 100, 2)
                    pps = round(self.pps * count / 100, 0)
                    imix_count[size] = pps
            self.rate = round(1342177280 / avg_size, 0) * 2
            logging.debug("Imax: %s rate: %s", imix_count, self.rate)
        return imix_count

    def get_streams(self, profile_data):
        """ generate trex stream
        :param profile_data:
        :type profile_data:
        """
        self.streams = []
        self.pps = self.params['traffic_profile'].get('frame_rate', 100)
        for packet_name in profile_data:
            outer_l2 = profile_data[packet_name].get('outer_l2')
            imix_data = self.generate_imix_data(outer_l2)
            if not imix_data:
                imix_data = {64: self.pps}
            self.generate_vm(profile_data[packet_name])
            for size in imix_data:
                self._generate_streams(size, imix_data[size])
        self._generate_profile()
        return self.profile

    def generate_vm(self, packet_definition):
        """ generate  trex vm with flows setup """
        self.ether_packet = Pkt.Ether()
        self.ip_packet = Pkt.IP()
        self.ip6_packet = None
        self.udp_packet = Pkt.UDP()
        self.udp_dport = 'UDP.dport'
        self.udp_sport = 'UDP.sport'
        self.qinq = False
        self.vm_flow_vars = []
        outer_l2 = packet_definition.get('outer_l2', None)
        outer_l3v4 = packet_definition.get('outer_l3v4', None)
        outer_l3v6 = packet_definition.get('outer_l3v6', None)
        outer_l4 = packet_definition.get('outer_l4', None)
        if outer_l2:
            self.set_outer_l2_fields(outer_l2)
        if outer_l3v4:
            self.set_outer_l3v4_fields(outer_l3v4)
        if outer_l3v6:
            self.set_outer_l3v6_fields(outer_l3v6)
        if outer_l4:
            self.set_outer_l4_fields(outer_l4)
        self.trex_vm = STLScVmRaw(self.vm_flow_vars)

    def generate_packets(self):
        """ generate packets from trex TG """
        base_pkt = self.base_pkt
        size = self.fsize - 4
        pad = max(0, size - len(base_pkt)) * 'x'
        self.packets = [STLPktBuilder(pkt=base_pkt / pad,
                                      vm=vm) for vm in self.vms]

    def _create_single_packet(self, size=64):
        size = size - 4
        ether_packet = self.ether_packet
        ip_packet = self.ip6_packet if self.ip6_packet else self.ip_packet
        udp_packet = self.udp_packet
        if self.qinq:
            qinq_packet = self.qinq_packet
            base_pkt = ether_packet / qinq_packet / ip_packet / udp_packet
        else:
            base_pkt = ether_packet / ip_packet / udp_packet
        pad = max(0, size - len(base_pkt)) * 'x'
        packet = STLPktBuilder(pkt=base_pkt / pad, vm=self.trex_vm)
        return packet

    def _create_single_stream(self, packet_size, pps, isg=0):
        packet = self._create_single_packet(packet_size)
        if self.pg_id:
            self.pg_id += 1
            stl_flow = STLFlowLatencyStats(pg_id=self.pg_id)
            stream = STLStream(isg=isg, packet=packet, mode=STLTXCont(pps=pps),
                               flow_stats=stl_flow)
        else:
            stream = STLStream(isg=isg, packet=packet, mode=STLTXCont(pps=pps))
        return stream

    def _generate_streams(self, packet_size, pps):
        self.streams.append(self._create_single_stream(packet_size, pps))

    def _generate_profile(self):
        self.profile = STLProfile(self.streams)

    @classmethod
    def _get_start_end_ipv6(cls, start_ip, end_ip):
        try:
            ip1 = socket.inet_pton(socket.AF_INET6, start_ip)
            ip2 = socket.inet_pton(socket.AF_INET6, end_ip)
            hi1, lo1 = struct.unpack('!QQ', ip1)
            hi2, lo2 = struct.unpack('!QQ', ip2)
            if ((hi1 << 64) | lo1) > ((hi2 << 64) | lo2):
                raise SystemExit("IPv6: start_ip is greater then end_ip")
            max_p1 = abs(int(lo1) - int(lo2))
            base_p1 = lo1
        except Exception as ex_error:
            raise SystemExit(ex_error)
        else:
            return base_p1, max_p1 + base_p1

    @classmethod
    def _get_random_value(cls, min_port, max_port):
        cryptogen = SystemRandom()
        return cryptogen.randrange(min_port, max_port)
