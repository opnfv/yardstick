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
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmWrFlowVar
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmFlowVarRepeatableRandom
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmFlowVar
from trex_stl_lib.trex_stl_packet_builder_scapy import STLVmFixIpv4
from trex_stl_lib import api as Pkt

from yardstick.common import exceptions as y_exc
from yardstick.network_services.traffic_profile import base


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
    RATE_ROUND = 5

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
        self.max_rate = 0
        self.min_rate = 0

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

    def _get_next_rate(self):
        rate = round(float(self.max_rate + self.min_rate)/2.0, self.RATE_ROUND)
        return rate

    def _get_framesize(self):
        framesizes = []
        for traffickey, value in self.params.items():
            if not traffickey.startswith((self.UPLINK, self.DOWNLINK)):
                continue
            for _, data in value.items():
                framesize = data['outer_l2']['framesize']
                for size in (s for s, w in framesize.items() if int(w) != 0):
                    framesizes.append(size)
        if len(set(framesizes)) == 0:
            return ''
        elif len(set(framesizes)) == 1:
            return framesizes[0]
        return 'IMIX'

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
