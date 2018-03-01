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

import struct
import socket
import logging
from random import SystemRandom
import ipaddress

import six

from yardstick.common import exceptions as y_exc
from yardstick.network_services.traffic_profile import base
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

SRC = 'src'
DST = 'dst'
ETHERNET = 'Ethernet'
IP = 'IP'
IPv6 = 'IPv6'
UDP = 'UDP'
DSCP = 'DSCP'
SRC_PORT = 'sport'
DST_PORT = 'dport'
TYPE_OF_SERVICE = 'tos'

LOG = logging.getLogger(__name__)


class TrexProfile(base.TrafficProfile):
    """ This class handles Trex Traffic profile generation and execution """

    PROTO_MAP = {
        ETHERNET: ('ether_packet', Pkt.Ether),
        IP: ('ip_packet', Pkt.IP),
        IPv6: ('ip6_packet', Pkt.IPv6),
        UDP: ('udp_packet', Pkt.UDP),
    }

    def _general_single_action_partial(self, protocol):
        def f(field):
            def partial(value):
                kwargs = {
                    field: value
                }
                self._set_proto_fields(protocol, **kwargs)
            return partial
        return f

    def _ethernet_range_action_partial(self, direction, _):
        def partial(min_value, max_value, count):
            # pylint: disable=unused-argument
            stl_vm_flow_var = STLVmFlowVar(name="mac_{}".format(direction),
                                           min_value=1,
                                           max_value=30,
                                           size=4,
                                           op='inc',
                                           step=1)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(
                fv_name='mac_{}'.format(direction),
                pkt_offset='Ether.{}'.format(direction))
            self.vm_flow_vars.append(stl_vm_wr_flow_var)
        return partial

    def _ip_range_action_partial(self, direction, count=1):
        # pylint: disable=unused-argument
        def partial(min_value, max_value, count):
            _, _, actual_count = self._count_ip(min_value, max_value)
            if not actual_count:
                count = 1
            elif actual_count < int(count):
                count = actual_count

            stl_vm_flow_var = STLVmFlowVarRepeatableRandom(
                name="ip4_{}".format(direction),
                min_value=min_value,
                max_value=max_value,
                size=4,
                limit=int(count),
                seed=0x1235)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(
                fv_name='ip4_{}'.format(direction),
                pkt_offset='IP.{}'.format(direction))
            self.vm_flow_vars.append(stl_vm_wr_flow_var)
            stl_vm_fix_ipv4 = STLVmFixIpv4(offset="IP")
            self.vm_flow_vars.append(stl_vm_fix_ipv4)
        return partial

    def _ip6_range_action_partial(self, direction, _):
        def partial(min_value, max_value, count):
            # pylint: disable=unused-argument
            min_value, max_value, _ = self._count_ip(min_value, max_value)
            stl_vm_flow_var = STLVmFlowVar(name="ip6_{}".format(direction),
                                           min_value=min_value,
                                           max_value=max_value,
                                           size=8,
                                           op='random',
                                           step=1)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(
                fv_name='ip6_{}'.format(direction),
                pkt_offset='IPv6.{}'.format(direction),
                offset_fixup=8)
            self.vm_flow_vars.append(stl_vm_wr_flow_var)
        return partial

    def _dscp_range_action_partial(self, *args):
        def partial(min_value, max_value, count):
            # pylint: disable=unused-argument
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
        return partial

    def _udp_range_action_partial(self, field, count=1):
        # pylint: disable=unused-argument
        def partial(min_value, max_value, count):
            actual_count = int(max_value) - int(min_value)
            if not actual_count:
                count = 1
            elif int(count) > actual_count:
                count = actual_count

            stl_vm_flow_var = STLVmFlowVarRepeatableRandom(
                name="port_{}".format(field),
                min_value=min_value,
                max_value=max_value,
                size=2,
                limit=int(count),
                seed=0x1235)
            self.vm_flow_vars.append(stl_vm_flow_var)
            stl_vm_wr_flow_var = STLVmWrFlowVar(
                fv_name='port_{}'.format(field),
                pkt_offset=self.udp[field])
            self.vm_flow_vars.append(stl_vm_wr_flow_var)
        return partial

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
        self.ether_packet = None
        self.ip_packet = None
        self.ip6_packet = None
        self.udp_packet = None
        self.udp = {
            SRC_PORT: '',
            DST_PORT: '',
        }
        self.qinq_packet = None
        self.qinq = False
        self.vm_flow_vars = []
        self.packets = []

        self._map_proto_actions = {
            # the tuple is (single value function, range value function, if the values should be
            # converted to integer).
            ETHERNET: (self._general_single_action_partial(ETHERNET),
                       self._ethernet_range_action_partial,
                       False,
                       ),
            IP: (self._general_single_action_partial(IP),
                 self._ip_range_action_partial,
                 False,
                 ),
            IPv6: (self._general_single_action_partial(IPv6),
                   self._ip6_range_action_partial,
                   False,
                   ),
            DSCP: (self._general_single_action_partial(IP),
                   self._dscp_range_action_partial,
                   True,
                   ),
            UDP: (self._general_single_action_partial(UDP),
                  self._udp_range_action_partial,
                  True,
                  ),
        }

    def execute_traffic(self, traffic_generator):
        """ Generate the stream and run traffic on the given ports """
        raise NotImplementedError()

    def _call_on_range(self, range, single_action, range_action, count=1, to_int=False):
        def convert_to_int(val):
            return int(val) if to_int else val

        range_iter = iter(str(range).split('-'))
        min_value = convert_to_int(next(range_iter))
        try:
            max_value = convert_to_int(next(range_iter))
        except StopIteration:
            single_action(min_value)
        else:
            range_action(min_value=min_value, max_value=max_value, count=count)

    def _set_proto_addr(self, protocol, field, address, count=1):
        single_action, range_action, to_int = self._map_proto_actions[protocol]
        self._call_on_range(address,
                            single_action(field),
                            range_action(field, count),
                            count=count,
                            to_int=to_int,
                            )

    def _set_proto_fields(self, protocol, **kwargs):
        _attr_name, _class = self.PROTO_MAP[protocol]

        if not getattr(self, _attr_name):
            setattr(self, _attr_name, _class())

        _attr = getattr(self, _attr_name)
        for key, value in six.iteritems(kwargs):
            setattr(_attr, key, value)

    def set_svlan_cvlan(self, svlan, cvlan):
        """ set svlan & cvlan """
        self.qinq = True
        ether_params = {'type': 0x8100}
        self._set_proto_fields(ETHERNET, **ether_params)
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

    def _set_outer_l2_fields(self, outer_l2):
        """ setup outer l2 fields from traffic profile """
        ether_params = {'type': 0x800}
        self._set_proto_fields(ETHERNET, **ether_params)
        if 'srcmac' in outer_l2:
            self._set_proto_addr(ETHERNET, SRC, outer_l2['srcmac'])
        if 'dstmac' in outer_l2:
            self._set_proto_addr(ETHERNET, DST, outer_l2['dstmac'])
        if 'QinQ' in outer_l2:
            self.set_qinq(outer_l2['QinQ'])

    def _set_outer_l3v4_fields(self, outer_l3v4):
        """ setup outer l3v4 fields from traffic profile """
        ip_params = {}
        if 'proto' in outer_l3v4:
            ip_params['proto'] = socket.getprotobyname(outer_l3v4['proto'])
            if outer_l3v4['proto'] == 'tcp':
                self.udp_packet = Pkt.TCP()
                self.udp[DST_PORT] = 'TCP.dport'
                self.udp[SRC_PORT] = 'TCP.sport'
                tcp_params = {'flags': '', 'window': 0}
                self._set_proto_fields(UDP, **tcp_params)
        if 'ttl' in outer_l3v4:
            ip_params['ttl'] = outer_l3v4['ttl']
        self._set_proto_fields(IP, **ip_params)
        if 'dscp' in outer_l3v4:
            self._set_proto_addr(DSCP, TYPE_OF_SERVICE, outer_l3v4['dscp'])
        if 'srcip4' in outer_l3v4:
            self._set_proto_addr(IP, SRC, outer_l3v4['srcip4'], outer_l3v4['count'])
        if 'dstip4' in outer_l3v4:
            self._set_proto_addr(IP, DST, outer_l3v4['dstip4'], outer_l3v4['count'])

    def _set_outer_l3v6_fields(self, outer_l3v6):
        """ setup outer l3v6 fields from traffic profile """
        ether_params = {'type': 0x86dd}
        self._set_proto_fields(ETHERNET, **ether_params)
        ip6_params = {}
        if 'proto' in outer_l3v6:
            ip6_params['proto'] = outer_l3v6['proto']
            if outer_l3v6['proto'] == 'tcp':
                self.udp_packet = Pkt.TCP()
                self.udp[DST_PORT] = 'TCP.dport'
                self.udp[SRC_PORT] = 'TCP.sport'
                tcp_params = {'flags': '', 'window': 0}
                self._set_proto_fields(UDP, **tcp_params)
        if 'ttl' in outer_l3v6:
            ip6_params['ttl'] = outer_l3v6['ttl']
        if 'tc' in outer_l3v6:
            ip6_params['tc'] = outer_l3v6['tc']
        if 'hlim' in outer_l3v6:
            ip6_params['hlim'] = outer_l3v6['hlim']
        self._set_proto_fields(IPv6, **ip6_params)
        if 'srcip6' in outer_l3v6:
            self._set_proto_addr(IPv6, SRC, outer_l3v6['srcip6'])
        if 'dstip6' in outer_l3v6:
            self._set_proto_addr(IPv6, DST, outer_l3v6['dstip6'])

    def _set_outer_l4_fields(self, outer_l4):
        """ setup outer l4 fields from traffic profile """
        if 'srcport' in outer_l4:
            self._set_proto_addr(UDP, SRC_PORT, outer_l4['srcport'], outer_l4['count'])
        if 'dstport' in outer_l4:
            self._set_proto_addr(UDP, DST_PORT, outer_l4['dstport'], outer_l4['count'])

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
        self.udp[DST_PORT] = 'UDP.dport'
        self.udp[SRC_PORT] = 'UDP.sport'
        self.qinq = False
        self.vm_flow_vars = []
        outer_l2 = packet_definition.get('outer_l2', None)
        outer_l3v4 = packet_definition.get('outer_l3v4', None)
        outer_l3v6 = packet_definition.get('outer_l3v6', None)
        outer_l4 = packet_definition.get('outer_l4', None)
        if outer_l2:
            self._set_outer_l2_fields(outer_l2)
        if outer_l3v4:
            self._set_outer_l3v4_fields(outer_l3v4)
        if outer_l3v6:
            self._set_outer_l3v6_fields(outer_l3v6)
        if outer_l4:
            self._set_outer_l4_fields(outer_l4)
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
    def _count_ip(cls, start_ip, end_ip):
        start = ipaddress.ip_address(six.u(start_ip))
        end = ipaddress.ip_address(six.u(end_ip))
        if start.version == 4:
            return start, end, int(end) - int(start)
        elif start.version == 6:
            if int(start) > int(end):
                raise y_exc.IPv6RangeError(start_ip=str(start),
                                           end_ip=str(end))
            _, lo1 = struct.unpack('!QQ', start.packed)
            _, lo2 = struct.unpack('!QQ', end.packed)
            return lo1, lo2, lo2 - lo1

    @classmethod
    def _get_random_value(cls, min_port, max_port):
        cryptogen = SystemRandom()
        return cryptogen.randrange(min_port, max_port)
