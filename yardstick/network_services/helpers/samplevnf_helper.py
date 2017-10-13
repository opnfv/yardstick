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


import copy
from collections import defaultdict, namedtuple
import ipaddress
from itertools import chain, repeat
import logging
import os
import re

import six

from yardstick.common.utils import ip_to_hex, try_int
from yardstick.network_services.helpers.iniparser import YardstickConfigParser

LOG = logging.getLogger(__name__)

LINK_CONFIG_TEMPLATE = """\
link {0} down
link {0} config {1} {2}
link {0} up
"""

# add comment string with syntax
ACTION_TEMPLATE = """\
# p action add <action-id> <action> <optional option>
p action add {action_id} accept
p action add {action_id} fwd {port_num}
p action add {action_id} count
"""

FW_ACTION_TEMPLATE = """\
# p action add <action-id> <action> <optional option>
p action add {action_id} accept
p action add {action_id} fwd {port_num}
p action add {action_id} count
p action add {action_id} conntrack
"""

# This sets up a basic passthrough with no rules
SCRIPT_TPL = """
{link_config}

# p <arpicmp_pipe_id> arpadd <interface_id> <ip_address in deciaml> <mac addr in hex>
{arp_config}

{arp_config6}

{arp_route_tbl}

{arp_route_tbl6}

{actions}

{rules}

"""


class PortPairs(object):

    DOWNLINK = "downlink"
    UPLINK = "uplink"

    def __init__(self, interfaces):
        super(PortPairs, self).__init__()
        self.interfaces = interfaces
        self._all_ports = None
        self._uplink_ports = None
        self._downlink_ports = None
        self._networks = None
        self._port_pair_list = None
        self._valid_networks = None

    @property
    def networks(self):
        if self._networks is None:
            self._networks = {}
            for intf in self.interfaces:
                vintf = intf['virtual-interface']
                try:
                    vld_id = vintf['vld_id']
                except KeyError:
                    # probably unused port?
                    LOG.warning("intf without vld_id, %s", vintf)
                else:
                    self._networks.setdefault(vld_id, []).append(vintf["ifname"])
        return self._networks

    @classmethod
    def get_downlink_id(cls, vld_id):
        # partition returns a tuple
        parts = list(vld_id.partition(cls.UPLINK))
        if parts[0]:
            # 'uplink' was not in or not leftmost in the string
            return
        parts[1] = cls.DOWNLINK
        public_id = ''.join(parts)
        return public_id

    @property
    # this only works for vnfs that have both uplink and public visible
    def valid_networks(self):
        if self._valid_networks is None:
            self._valid_networks = []
            for vld_id in self.networks:
                downlink_id = self.get_downlink_id(vld_id)
                if downlink_id in self.networks:
                    self._valid_networks.append((vld_id, downlink_id))
        return self._valid_networks

    @property
    def all_ports(self):
        if self._all_ports is None:
            self._all_ports = sorted(set(self.uplink_ports + self.downlink_ports))
        return self._all_ports

    @property
    def uplink_ports(self):
        if self._uplink_ports is None:
            intfs = chain.from_iterable(
                intfs for vld_id, intfs in self.networks.items() if
                vld_id.startswith(self.UPLINK))
            self._uplink_ports = sorted(set(intfs))
        return self._uplink_ports

    @property
    def downlink_ports(self):
        if self._downlink_ports is None:
            intfs = chain.from_iterable(
                intfs for vld_id, intfs in self.networks.items() if
                vld_id.startswith(self.DOWNLINK))
            self._downlink_ports = sorted(set(intfs))
        return self._downlink_ports

    @property
    def port_pair_list(self):
        if self._port_pair_list is None:
            self._port_pair_list = []

            for uplink, downlink in self.valid_networks:
                for uplink_intf in self.networks[uplink]:
                    # only VNFs have uplink, public peers
                    peer_intfs = self.networks.get(downlink, [])
                    if peer_intfs:
                        for downlink_intf in peer_intfs:
                            port_pair = uplink_intf, downlink_intf
                            self._port_pair_list.append(port_pair)
        return self._port_pair_list


class Core(namedtuple('CoreTuple', 'socket, core, hyperthread')):
    CORE_RE = re.compile(r"^(?:s(?P<socket>\d+))?c?(?P<core>\d+)(?P<hyperthread>h)?$")

    def __new__(cls, socket=None, core=None, hyperthread=''):
        try:
            if socket and core is None and hyperthread == '':
                    # first arg is a string
                    matches = cls.CORE_RE.search(str(socket))
                    if matches:
                        m = matches.groupdict()
                        socket = m['socket']
                        core = m['core']
                        hyperthread = m['hyperthread']
            socket = try_int(socket, 0)
            # fail if not int
            core = int(core)

            if hyperthread in {1, '1', True, 'h'}:
                hyperthread = "h"
            else:
                hyperthread = ""

            return super(Core, cls).__new__(cls, socket, core, hyperthread)

        except (AttributeError, TypeError, IndexError, ValueError):
            raise ValueError(
                'Invalid core spec socket={} core={} hyperthread={}'.format(socket, core,
                                                                            hyperthread))

    def is_hyperthread(self):
        return self.hyperthread == 'h'

    def make_hyperthread(self):
        return self.__new__(self.__class__, self.socket, self.core, "h")

    def __str__(self):
        if self.socket != 0:
            s = "s{}c{}".format(self.socket, self.core)
        else:
            s = self.core
        return "{}{}".format(s, self.hyperthread)

    def __add__(self, other):
        # when we increment we reset hyperthread
        return self.__new__(self.__class__, self.socket, self.core + other, "")

    def __sub__(self, other):
        # when we decrement we reset hyperthread
        return self.__new__(self.__class__, self.socket, self.core - other, "")

    def __iadd__(self, other):
        # when we increment we reset hyperthread
        return self.__new__(self.__class__, self.socket, self.core + other, "")

    def __isub__(self, other):
        # when we decrement we reset hyperthread
        return self.__new__(self.__class__, self.socket, self.core - other, "")


class MultiPortConfig(object):

    HW_LB = "HW"

    @staticmethod
    def float_x_plus_one_tenth_of_y(x, y):
        return float(x) + float(y) / 10.0

    @staticmethod
    def make_str(base, iterator):
        return ' '.join((base.format(x) for x in iterator))

    @classmethod
    def make_range_str(cls, base, start, stop=0, offset=0):
        if offset and not stop:
            stop = start + offset
        return cls.make_str(base, range(start, stop))

    @staticmethod
    def make_ip_addr(ip, mask):
        """
        :param ip: ip adddress
        :type ip: str
        :param mask: /24 prefix of 255.255.255.0 netmask
        :type mask: str
        :return: interface
        :rtype: IPv4Interface
        """

        try:
            return ipaddress.ip_interface(six.text_type('/'.join([ip, mask])))
        except (TypeError, ValueError):
            # None so we can skip later
            return None

    @classmethod
    def validate_ip_and_prefixlen(cls, ip_addr, prefixlen):
        ip_addr = cls.make_ip_addr(ip_addr, prefixlen)
        return ip_addr.ip.exploded, ip_addr.network.prefixlen

    def __init__(self, scenario_helper, config_tpl, tmp_file, vnfd_helper, vnf_type, core_map,
                 socket=0):

        super(MultiPortConfig, self).__init__()
        self.scenario_helper = scenario_helper
        self.vnf_cfg = self.scenario_helper.vnf_cfg
        self.worker_config = self.vnf_cfg.get('worker_config', '1C/1T').split('/')[1].lower()
        self.worker_threads = self.get_worker_threads(self.vnf_cfg.get('worker_threads', 3))
        self.txrx_mode = self.vnf_cfg.get('txrx_mode', 'share')
        self.lb_count = int(self.vnf_cfg.get('lb_count', 3))
        self.lb_config = self.vnf_cfg.get('lb_config', 'SW')
        self.vnf_type = vnf_type
        self.core_map = core_map
        self.pipe_line = 0
        self.vnfd_helper = vnfd_helper
        # disable semi-colon comments, because we use junk like
        # outport_offset = 136; 8
        # hash_offset = 200;72
        self.write_parser = YardstickConfigParser(equal_sep=' ', semi='')
        self.read_parser = YardstickConfigParser(semi='')
        self.read_parser.read(config_tpl)
        # set socket first
        self.socket = socket
        self.master_core = Core(socket=self.socket,
                                core=self.read_parser.get("PIPELINE0", "core", 0))
        self.master_tpl = self.get_config_tpl_data('MASTER')
        self.arpicmp_tpl = self.get_config_tpl_data('ARPICMP')
        self.txrx_tpl = self.get_config_tpl_data('TXRX')
        self.loadb_tpl = self.get_config_tpl_data('LOADB')
        self.vnf_tpl = self.get_config_tpl_data(vnf_type)
        self.swq = 0
        self.tmp_file = os.path.join("/tmp", tmp_file)
        self.pktq_out_os = []
        self.start_core = None
        self.pipeline_counter = None
        self.txrx_pipeline = None
        self.arpicmp_pipeline = None
        self._port_pairs = None
        self.all_ports = []
        self.port_to_action_map = {}
        self.port_pair_list = []
        self.lb_to_port_pair_mapping = {}

        self.lb_index = None
        self.mul = 0
        self.port_pairs = []
        self.ports_len = 0
        self.prv_que_handler = None
        self.vnfd = None
        self.rules = None
        self.pktq_out = []

    def make_port_pairs_iter(self, operand, iterable):
        return (operand(self.vnfd_helper.port_num(x), y) for y in iterable for x in
                chain.from_iterable(self.port_pairs))

    def make_range_port_pairs_iter(self, operand, start, end):
        return self.make_port_pairs_iter(operand, range(start, end))

    def init_eal(self):
        # only use ports in the topology
        intfs = (self.vnfd_helper.find_interface(name=port) for port in
                 self.vnfd_helper.port_pairs.all_ports)
        vpci = (intf['virtual-interface']["vpci"] for intf in intfs)
        lines = [['w', item] for item in vpci]
        section = ["EAL", lines]
        self.write_parser.sections.insert(0, section)

    def add_updated_timer(self):
        timer_tpl = self.get_config_tpl_data('TIMER')
        self.write_parser.section_set_value(timer_tpl, 'core', str(Core(self.socket, 0)),
                                            set_all=True)
        # reset pipeline number
        timer_tpl[0] = "PIPELINE{0}".format(self.pipeline_counter)
        self.write_parser.sections.append(timer_tpl)

    def get_config_tpl_data(self, type_value):
        for section in self.read_parser:
            if any(type_value == val for key, val in section[1] if key == 'type'):
                return section

    def get_txrx_tpl_data(self, value):
        for section in self.read_parser:
            if any(value == val for key, val in section[1] if key == 'pipeline_txrx_type'):
                return section

    PIPELINE_RE = re.compile(r"PIPELINE(\d+)")

    def find_pipeline_indexes(self):
        for section in self.read_parser:
            section_type = self.read_parser.section_get(section, 'type', None)
            if 'ARPICMP' == section_type:
                # this is pipeline number, not core?
                # self.pipeline_counter = Core(self.socket,
                #                              self.read_parser.section_get(section, 'core'))
                self.arpicmp_pipeline = int(self.PIPELINE_RE.search(section[0]).group(1))
                self.pipeline_counter = self.arpicmp_pipeline + 1
            # this won't work because TXRX is allocated last
            # if 'TXRX' == section_type:
            #     self.txrx_pipeline = int(self.PIPELINE_RE.search(section[0]).group(1))
                # self.txrx_pipeline = Core(self.socket,
                #                           self.read_parser.section_get(section, 'core'))

    def new_pipeline(self, tpl_section, new_data):
        new_section = copy.deepcopy(tpl_section)
        new_section[0] = "PIPELINE{0}".format(self.pipeline_counter)
        # increment pipeline_counter here where we add the section
        self.pipeline_counter += 1
        self.write_parser.update_section_data(new_section, new_data)
        return new_section

    def get_worker_threads(self, worker_threads):
        if self.worker_config == '1t':
            return worker_threads
        else:
            return worker_threads - worker_threads % 2

    def generate_rxrx_core_id(self, core, mode):
        # hyperthreaded
        if int(self.core_map["thread_per_core"]) > 1 and not self.start_core.is_hyperthread():
            return core.make_hyperthread(), core + 1
        # hyperthread is not enabled
        else:
            # share the same core for TX and RX
            if mode == "share":
                return core, core + 1
            # place RXRX on next core
            elif mode == "next":
                return core + 1, core + 2

    def generate_next_core_id(self, core):
        if self.worker_config == '1t':
            return core + 1

        # hyperthread is not enabled
        if int(self.core_map["thread_per_core"]) == 1:
            return core + 1

        if self.start_core.is_hyperthread():
            # move to the next core
            return core + 1
        else:
            return core.make_hyperthread()

    def get_lb_count(self):
        self.lb_count = int(min(len(self.port_pair_list), self.lb_count))

    def generate_lb_to_port_pair_mapping(self):
        self.lb_to_port_pair_mapping = defaultdict(int)
        port_pair_count = len(self.port_pair_list)
        lb_pair_count = int(port_pair_count / self.lb_count)
        extra = port_pair_count % self.lb_count
        extra_iter = repeat(lb_pair_count + 1, extra)
        norm_iter = repeat(lb_pair_count, port_pair_count - extra)
        new_values = {i: v for i, v in enumerate(chain(extra_iter, norm_iter), 1)}
        self.lb_to_port_pair_mapping.update(new_values)

    def set_priv_to_pub_mapping(self):
        port_nums = [tuple(self.vnfd_helper.port_nums(x)) for x in self.port_pair_list]
        return "".join(str(y).replace(" ", "") for y in port_nums)

    def set_priv_que_handler(self):
        # iterated twice, can't be generator
        priv_to_pub_map = [tuple(self.vnfd_helper.port_nums(x)) for x in self.port_pairs]
        # must be list to use .index()
        port_list = list(chain.from_iterable(priv_to_pub_map))
        uplink_ports = (x[0] for x in priv_to_pub_map)
        self.prv_que_handler = '({})'.format(
            "".join(("{},".format(port_list.index(x)) for x in uplink_ports)))

    def generate_arp_route_tbl(self):
        arp_route_tbl_tmpl = "routeadd net {port_num} {port_dst_ip} 0x{port_netmask_hex}"

        def build_arp_config(port):
            dpdk_port_num = self.vnfd_helper.port_num(port)
            interface = self.vnfd_helper.find_interface(name=port)["virtual-interface"]
            # We must use the dst because we are on the VNF and we need to
            # reach the TG.
            dst_port_ip = ipaddress.ip_interface(six.text_type(
                "%s/%s" % (interface["dst_ip"], interface["netmask"])))

            arp_vars = {
                "port_netmask_hex": ip_to_hex(dst_port_ip.network.netmask.exploded),
                # this is the port num that contains port0 subnet and next_hop_ip_hex
                # this is LINKID which should be based on DPDK port number
                "port_num": dpdk_port_num,
                # next hop is dst in this case
                # must be within subnet
                "port_dst_ip": str(dst_port_ip.ip),
            }
            return arp_route_tbl_tmpl.format(**arp_vars)

        return '\n'.join(build_arp_config(port) for port in self.all_ports)

    def generate_arpicmp_data(self, core):
        pkqt_in = self.make_range_str('SWQ{}', self.swq, offset=self.lb_count)
        self.swq += self.lb_count
        pktq_out = self.make_range_str('SWQ{}', self.swq, offset=self.lb_count)
        self.swq += self.lb_count
        # ports_mac_list is disabled for some reason

        # mac_iter = (self.vnfd_helper.find_interface(name=port)['virtual-interface']['local_mac']
        #             for port in self.all_ports)
        pktq_in_iter = ('RXQ{}.0'.format(self.vnfd_helper.port_num(x[0])) for x in
                        self.port_pair_list)

        self.pktq_out_os = pktq_out.split(' ')
        # HWLB is a run to compelition? So override the pktq_in/pktq_out
        if self.lb_config == self.HW_LB:
            self.swq = 0
            pkqt_in = \
                self.make_range_str('SWQ{}', self.swq,
                                    offset=(self.lb_count * self.worker_threads))
            # WA: Since port_pairs will not be populated during arp pipeline
            self.port_pairs = self.port_pair_list
            port_iter = \
                self.make_port_pairs_iter(self.float_x_plus_one_tenth_of_y, [self.mul])
            pktq_out = self.make_str('TXQ{}', port_iter)
        arpicmp_data = [
            ['type', 'ARPICMP'],
            ['core', core],
            ['pktq_in', pkqt_in],
            ['pktq_out', pktq_out],
            # we need to disable ports_mac_list?
            # it looks like ports_mac_list is no longer required
            # ['ports_mac_list', ' '.join(mac_iter)],
            ['pktq_in_prv', ' '.join(pktq_in_iter)],
            ['prv_to_pub_map', self.set_priv_to_pub_mapping()],
            # DO NOT USE arp_route_tbl, use routeadd command
            # ['arp_route_tbl', ],
            # nd_route_tbl must be set or we get segault on random OpenStack IPv6 traffic
            # safe default?  route discard prefix to localhost
            ['nd_route_tbl', "(0100::,64,0,::1)"],
        ]

        return arpicmp_data

    def generate_final_txrx_data(self, core):
        swq_start = self.swq - self.ports_len * self.worker_threads

        txq_start = 0
        txq_end = self.worker_threads

        pktq_out_iter = self.make_range_port_pairs_iter(self.float_x_plus_one_tenth_of_y,
                                                        txq_start, txq_end)

        pktq_out = self.make_str('TXQ{}', pktq_out_iter)
        pktq_in = self.make_range_str('SWQ{}', swq_start, self.swq)
        pktq_in = '{0} {1}'.format(pktq_in, self.pktq_out_os[self.lb_index - 1])
        rxtx_data = [
            ['pktq_in', pktq_in],
            ['pktq_out', pktq_out],
            ['pipeline_txrx_type', 'TXTX'],
            ['core', core],
        ]
        return rxtx_data

    def generate_initial_txrx_data(self, core):
        pktq_iter = self.make_range_port_pairs_iter(self.float_x_plus_one_tenth_of_y,
                                                    0, self.worker_threads)

        rxq_str = self.make_str('RXQ{}', pktq_iter)
        swq_str = self.make_range_str('SWQ{}', self.swq, offset=self.ports_len)
        txrx_data = [
            ['type', 'TXRX'],
            ['pipeline_txrx_type', 'RXRX'],
            ['dest_if_offset', 176],
            ['core', core],
            ['pktq_in', rxq_str],
            ['pktq_out', swq_str + ' SWQ{0}'.format(self.lb_index - 1)],
        ]
        return txrx_data

    def generate_lb_data(self, core):
        pktq_in = self.make_range_str('SWQ{}', self.swq, offset=self.ports_len)
        self.swq += self.ports_len

        offset = self.ports_len * self.worker_threads
        pktq_out = self.make_range_str('SWQ{}', self.swq, offset=offset)
        self.pktq_out = pktq_out.split()

        self.swq += (self.ports_len * self.worker_threads)
        lb_data = [
            ['type', 'LOADB'],
            ['core', core],
            ['pktq_in', pktq_in],
            ['pktq_out', pktq_out],
            ['n_vnf_threads', str(self.worker_threads)],
            ['prv_que_handler', self.prv_que_handler],
        ]
        return lb_data

    def generate_vnf_data(self, core):
        if self.lb_config == self.HW_LB:
            port_iter = self.make_port_pairs_iter(self.float_x_plus_one_tenth_of_y, [self.mul])
            pktq_in = self.make_str('RXQ{}', port_iter)

            self.mul += 1
            port_iter = self.make_port_pairs_iter(self.float_x_plus_one_tenth_of_y, [self.mul])
            pktq_out = self.make_str('TXQ{}', port_iter)

            pipe_line_data = [
                ['pktq_in', pktq_in],
                ['pktq_out', pktq_out + ' SWQ{0}'.format(self.swq)],
                ['prv_que_handler', self.prv_que_handler],
                ['core', core],
            ]
            self.swq += 1
        else:
            pipe_line_data = [
                ['pktq_in', ' '.join((self.pktq_out.pop(0) for _ in range(self.ports_len)))],
                ['pktq_out', self.make_range_str('SWQ{}', self.swq, offset=self.ports_len)],
                ['prv_que_handler', self.prv_que_handler],
                ['core', core],
            ]
            self.swq += self.ports_len

        if self.vnf_type in ('ACL', 'VFW'):
            pipe_line_data[:] = [item for item in pipe_line_data if item[0] != 'prv_que_handler']

        if self.read_parser.section_get(self.vnf_tpl, 'vnf_set', None):
            public_ip_port_range_list = self.read_parser.section_get(
                self.vnf_tpl, 'public_ip_port_range').split(':')
            ip_in_hex = '{:x}'.format(int(public_ip_port_range_list[0], 16) + self.lb_index - 1)
            public_ip_port_range_list[0] = ip_in_hex
            self.read_parser.section_set_value(self.vnf_tpl, 'public_ip_port_range',
                                               ':'.join(public_ip_port_range_list), set_all=True)

        return pipe_line_data

    def generate_config_data(self):
        # copy over MASTER and ARPICMP
        self.init_eal()
        self.find_pipeline_indexes()

        # use master core for master, don't use self.start_core
        self.write_parser.section_set_value(self.master_tpl, 'core',
                                            str(self.master_core), set_all=True)
        # mutate original sections and append
        self.write_parser.sections.append(self.master_tpl)
        # always put ARP on master core?
        self.write_parser.update_section_data(self.arpicmp_tpl,
                                              self.generate_arpicmp_data(self.master_core))
        self.write_parser.sections.append(self.arpicmp_tpl)
        self.start_core = self.master_core + 1

        if self.vnf_type == 'CGNAPT':
            self.add_updated_timer()
            self.pipeline_counter += 1

        rxrx_data = []
        txrx_data = []

        new_pipelines = []
        # create this section first, then we have to update it
        rxrx_section = self.new_pipeline(self.txrx_tpl, {})
        for lb in self.lb_to_port_pair_mapping:
            self.lb_index = lb
            self.mul = 0
            port_pair_count = self.lb_to_port_pair_mapping[lb]
            if not self.port_pair_list:
                continue

            self.port_pairs = self.port_pair_list[:port_pair_count]
            self.port_pair_list = self.port_pair_list[port_pair_count:]
            self.ports_len = port_pair_count * 2
            self.set_priv_que_handler()
            # we are always SW LB in OpenStack instances
            if self.lb_config == 'SW':
                rxrx_data = self.generate_initial_txrx_data(self.start_core)
                # reserve core for final txrx
                final_txrx_core, self.start_core = self.generate_rxrx_core_id(self.start_core,
                                                                              self.txrx_mode)
                lb_data = self.generate_lb_data(self.start_core)
                new_pipelines.append(self.new_pipeline(self.loadb_tpl, lb_data))
                self.start_core += 1
            else:
                # why? we don't use final_txrx_core if not SW LB
                # make pylint happy
                final_txrx_core = self.start_core + 1

            for _ in range(self.worker_threads):
                vnf_data = self.generate_vnf_data(self.start_core)
                if not self.vnf_tpl:
                    self.vnf_tpl = {}
                new_pipelines.append(self.new_pipeline(self.vnf_tpl, vnf_data))
                try:
                    self.write_parser.section_get(self.vnf_tpl, 'vnf_set')
                    self.write_parser.section_del(self.vnf_tpl, 'vnf_set')
                except KeyError:
                    pass
                else:
                    self.write_parser.section_del(self.vnf_tpl, 'public_ip_port_range')
                self.start_core = self.generate_next_core_id(self.start_core)

            if self.lb_config == 'SW':
                # this must happen here because we increment self.swq
                txrx_data = self.generate_final_txrx_data(final_txrx_core)
            self.vnf_tpl = self.get_config_tpl_data(self.vnf_type)
        # update only to preserve PIPELINE number
        self.write_parser.update_section_data(rxrx_section, rxrx_data)
        self.write_parser.sections.append(rxrx_section)
        # write the new sections last
        self.write_parser.sections.extend(new_pipelines)
        # add final pipeline last since we are using lists and order matters
        self.write_parser.sections.append(self.new_pipeline(self.txrx_tpl, txrx_data))

    def generate_config(self):
        self._port_pairs = PortPairs(self.vnfd_helper.interfaces)
        self.port_pair_list = self._port_pairs.port_pair_list
        self.all_ports = self._port_pairs.all_ports
        # create map from port to action_id using index
        self.port_to_action_map = {p: i for i, p in
                                   enumerate(self.vnfd_helper.port_nums(self.all_ports))}

        self.get_lb_count()
        self.generate_lb_to_port_pair_mapping()
        self.generate_config_data()
        # self.read_parser.write(sys.stdout)
        with open(self.tmp_file, 'w') as tfh:
            self.write_parser.write(tfh)

    def generate_link_config(self):
        def build_args(port):
            # lookup interface by name
            virtual_interface = self.vnfd_helper.find_interface(name=port)["virtual-interface"]
            local_ip = virtual_interface["local_ip"]
            netmask = virtual_interface["netmask"]
            port_num = self.vnfd_helper.port_num(port)
            port_ip, prefix_len = self.validate_ip_and_prefixlen(local_ip, netmask)
            return LINK_CONFIG_TEMPLATE.format(port_num, port_ip, prefix_len)

        return ''.join(build_args(port) for port in self.all_ports)

    def get_route_data(self, src_key, data_key, port):
        route_list = self.vnfd['vdu'][0].get(src_key, [])
        try:
            return next((route[data_key] for route in route_list if route['if'] == port), None)
        except (TypeError, StopIteration, KeyError):
            return None

    def get_ports_gateway(self, port):
        return self.get_route_data('routing_table', 'gateway', port)

    def get_ports_gateway6(self, port):
        return self.get_route_data('nd_route_tbl', 'gateway', port)

    def get_netmask_gateway(self, port):
        return self.get_route_data('routing_table', 'netmask', port)

    def get_netmask_gateway6(self, port):
        return self.get_route_data('nd_route_tbl', 'netmask', port)

    def generate_arp_config(self):
        arp_config = []
        for port in self.all_ports:
            # ignore gateway, always use TG IP, assume next hop is TG
            # gateway = self.get_ports_gateway(port)
            vintf = self.vnfd_helper.find_interface(name=port)["virtual-interface"]
            dst_mac = vintf["dst_mac"]
            dst_ip = vintf["dst_ip"]
            # so dst_mac is the TG dest mac, so we need TG dest IP.
            arp_config.append({
                "port_num": self.vnfd_helper.port_num(port),
                "dst_ip": dst_ip,
                "dst_mac": dst_mac,
                "arpicmp_pipe_id": self.arpicmp_pipeline,
            }
            )

        return '\n'.join(
            ('p {arpicmp_pipe_id} arpadd {port_num} {dst_ip} {dst_mac}'.format(**values) for values
             in arp_config))

    def generate_arp_config6(self):
        arp_config6 = []
        for port in self.all_ports:
            # ignore gateway, always use TG IP, assume next hop is TG
            # gateway6 = self.get_ports_gateway6(port)
            vintf = self.vnfd_helper.find_interface(name=port)["virtual-interface"]
            dst_mac6 = vintf["dst_mac"]
            dst_ip6 = vintf["dst_ip"]
            arp_config6.append({
                "port_num": self.vnfd_helper.port_num(port),
                "dst_ip": dst_ip6,
                "dst_mac": dst_mac6,
                "arpicmp_pipe_id": self.arpicmp_pipeline,
            }
            )

        return '\n'.join(
            ('p {arpicmp_pipe_id} arpadd {port_num} {dst_ip} {dst_mac}'.format(**values) for values
             in arp_config6))

    def generate_action_config(self):
        port_list = (self.vnfd_helper.port_num(p) for p in self.all_ports)
        if self.vnf_type == "VFW":
            template = FW_ACTION_TEMPLATE
        else:
            template = ACTION_TEMPLATE

        return ''.join(
            (template.format(action_id=self.port_to_action_map[port], port_num=port) for port in
             port_list))

    def get_ip_from_port(self, port):
        # we can't use gateway because in OpenStack gateways interfer with floating ip routing
        # return self.make_ip_addr(self.get_ports_gateway(port), self.get_netmask_gateway(port))
        vintf = self.vnfd_helper.find_interface(name=port)["virtual-interface"]
        ip = vintf["local_ip"]
        netmask = vintf["netmask"]
        return self.make_ip_addr(ip, netmask)

    def get_network_and_prefixlen_from_ip_of_port(self, port):
        ip_addr = self.get_ip_from_port(port)
        # handle cases with no gateway
        if ip_addr:
            return ip_addr.network.network_address.exploded, ip_addr.network.prefixlen
        else:
            return None, None

    def generate_rule_config(self):
        cmd = 'acl' if self.vnf_type == "ACL" else "vfw"
        rules_config = self.rules if self.rules else ''
        new_rules = []
        new_ipv6_rules = []
        # pattern = 'p {0} add {1} {2} {3} {4} {5} 0 65535 0 65535 0 0 {6}'
        pattern = 'p {cmd} add {priority} {src_ip} {src_mask} {dst_ip} {dst_mask} {' \
                  'src_port_from} {src_port_to} {dst_port_from} {dst_port_to} {protocol} {' \
                  'protocol_mask} {action_id}'
        for src_intf, dst_intf in self.port_pair_list:
            src_port = self.vnfd_helper.port_num(src_intf)
            dst_port = self.vnfd_helper.port_num(dst_intf)

            src_net, src_prefix_len = self.get_network_and_prefixlen_from_ip_of_port(src_intf)
            dst_net, dst_prefix_len = self.get_network_and_prefixlen_from_ip_of_port(dst_intf)
            # ignore entires with empty values
            if all((src_net, src_prefix_len, dst_net, dst_prefix_len)):
                # new_rules.append((cmd, self.txrx_pipeline, src_net, src_prefix_len,
                #                   dst_net, dst_prefix_len, dst_port))
                new_rules.append({
                    "cmd": cmd,
                    "priority": self.arpicmp_pipeline,
                    "src_ip": src_net,
                    "src_mask": src_prefix_len,
                    "dst_ip": dst_net,
                    "dst_mask": dst_prefix_len,
                    "src_port_from": 0,
                    "src_port_to": 65535,
                    "dst_port_from": 0,
                    "dst_port_to": 65535,
                    "protocol": 0,
                    "protocol_mask": 0,
                    "action_id": self.port_to_action_map[dst_port],
                })
                # swap src and dst
                # new_rules.append((cmd, self.txrx_pipeline, dst_net, dst_prefix_len,
                #                   src_net, src_prefix_len, src_port))
                new_rules.append({
                    "cmd": cmd,
                    "priority": self.arpicmp_pipeline,
                    "src_ip": dst_net,
                    "src_mask": dst_prefix_len,
                    "dst_ip": src_net,
                    "dst_mask": src_prefix_len,
                    "src_port_from": 0,
                    "src_port_to": 65535,
                    "dst_port_from": 0,
                    "dst_port_to": 65535,
                    "protocol": 0,
                    "protocol_mask": 0,
                    "action_id": self.port_to_action_map[src_port],
                })

            # src_net = self.get_ports_gateway6(port_pair[0])
            # src_prefix_len = self.get_netmask_gateway6(port_pair[0])
            # dst_net = self.get_ports_gateway6(port_pair[1])
            # dst_prefix_len = self.get_netmask_gateway6(port_pair[0])
            # # ignore entires with empty values
            # if all((src_net, src_prefix_len, dst_net, dst_prefix_len)):
            #     new_ipv6_rules.append((cmd, self.txrx_pipeline, src_net, src_prefix_len,
            #                            dst_net, dst_prefix_len, dst_port))
            #     new_ipv6_rules.append((cmd, self.txrx_pipeline, dst_net, dst_prefix_len,
            #                            src_net, src_prefix_len, src_port))

        acl_apply = "\np %s applyruleset" % cmd
        # add comment string with syntax
        doc_string = "# p acl add <priority> <src-ip> <mask> <dst-ip> <mask> <src-port-from> " \
                     "<src-port-to> <dst-port-from> <dst-port-to> <protocol> <protocol-mask> " \
                     "<action-id>\n"
        new_rules_config = '\n'.join(pattern.format(**values) for values
                                     in chain(new_rules, new_ipv6_rules))
        return ''.join(chain(rules_config, doc_string, new_rules_config, acl_apply))

    def generate_script_data(self):
        self._port_pairs = PortPairs(self.vnfd_helper.interfaces)
        self.port_pair_list = self._port_pairs.port_pair_list
        self.get_lb_count()
        script_data = {
            'link_config': self.generate_link_config(),
            'arp_config': self.generate_arp_config(),
            # disable IPv6 for now
            'arp_config6': "",
            'arp_route_tbl': self.generate_arp_route_tbl(),
            'arp_route_tbl6': "",
            'actions': '',
            'rules': '',
        }

        if self.vnf_type in ('ACL', 'VFW'):
            script_data.update({
                'actions': self.generate_action_config(),
                'rules': self.generate_rule_config(),
            })

        return script_data

    def generate_script(self, vnfd, rules=None):
        self.vnfd = vnfd
        self.rules = rules
        script_data = self.generate_script_data()
        script = SCRIPT_TPL.format(**script_data)
        if self.lb_config == self.HW_LB:
            script += 'set fwd rxonly'
            hwlb_tpl = """
set_sym_hash_ena_per_port {0} enable
set_hash_global_config {0} simple_xor ipv4-udp enable
set_sym_hash_ena_per_port {1} enable
set_hash_global_config {1} simple_xor ipv4-udp enable
set_hash_input_set {0} ipv4-udp src-ipv4 udp-src-port add
set_hash_input_set {1} ipv4-udp dst-ipv4 udp-dst-port add
set_hash_input_set {0} ipv6-udp src-ipv6 udp-src-port add
set_hash_input_set {1} ipv6-udp dst-ipv6 udp-dst-port add
"""
            for port_pair in self.port_pair_list:
                script += hwlb_tpl.format(*(self.vnfd_helper.port_nums(port_pair)))
        return script
