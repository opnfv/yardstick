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

from __future__ import absolute_import

import ipaddress
import logging
import os
import sys
from collections import OrderedDict, defaultdict
from itertools import chain

import six
from six.moves.configparser import ConfigParser

from yardstick.common.utils import ip_to_hex

LOG = logging.getLogger(__name__)

LINK_CONFIG_TEMPLATE = """\
link {0} down
link {0} config {1} {2}
link {0} up
"""

ACTION_TEMPLATE = """\
p action add {0} accept
p action add {0} fwd {0}
p action add {0} count
"""

FW_ACTION_TEMPLATE = """\
p action add {0} accept
p action add {0} fwd {0}
p action add {0} count
p action add {0} conntrack
"""

# This sets up a basic passthrough with no rules
SCRIPT_TPL = """
{link_config}

{arp_config}

{arp_config6}

{actions}

{rules}

"""


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
    def parser_get(parser, section, key, default=None):
        if parser.has_option(section, key):
            return parser.get(section, key)
        return default

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

    def __init__(self, topology_file, config_tpl, tmp_file, interfaces=None,
                 vnf_type='CGNAT', lb_count=2, worker_threads=3,
                 worker_config='1C/1T', lb_config='SW', socket=0):

        super(MultiPortConfig, self).__init__()
        self.topology_file = topology_file
        self.worker_config = worker_config.split('/')[1].lower()
        self.worker_threads = self.get_worker_threads(worker_threads)
        self.vnf_type = vnf_type
        self.pipe_line = 0
        self.interfaces = interfaces if interfaces else {}
        self.networks = {}
        self.write_parser = ConfigParser()
        self.read_parser = ConfigParser()
        self.read_parser.read(config_tpl)
        self.master_core = self.read_parser.get("PIPELINE0", "core")
        self.master_tpl = self.get_config_tpl_data('MASTER')
        self.arpicmp_tpl = self.get_config_tpl_data('ARPICMP')
        self.txrx_tpl = self.get_config_tpl_data('TXRX')
        self.loadb_tpl = self.get_config_tpl_data('LOADB')
        self.vnf_tpl = self.get_config_tpl_data(vnf_type)
        self.swq = 0
        self.lb_count = int(lb_count)
        self.lb_config = lb_config
        self.tmp_file = os.path.join("/tmp", tmp_file)
        self.pktq_out_os = []
        self.socket = socket
        self.start_core = ""
        self.pipeline_counter = ""
        self.txrx_pipeline = ""
        self.port_pair_list = []
        self.lb_to_port_pair_mapping = {}
        self.init_eal()

        self.lb_index = None
        self.mul = 0
        self.port_pairs = []
        self.port_pair_list = []
        self.ports_len = 0
        self.prv_que_handler = None
        self.vnfd = None
        self.rules = None
        self.pktq_out = ''

    @staticmethod
    def gen_core(core):
        # return "s{}c{}".format(self.socket, core)
        # don't use sockets for VNFs, because we don't want to have to
        # adjust VM CPU topology.  It is virtual anyway
        return str(core)

    def make_port_pairs_iter(self, operand, iterable):
        return (operand(x[-1], y) for y in iterable for x in chain(*self.port_pairs))

    def make_range_port_pairs_iter(self, operand, start, end):
        return self.make_port_pairs_iter(operand, range(start, end))

    def init_eal(self):
        vpci = [v['virtual-interface']["vpci"] for v in self.interfaces]
        with open(self.tmp_file, 'w') as fh:
            fh.write('[EAL]\n')
            for item in vpci:
                fh.write('w = {0}\n'.format(item))
            fh.write('\n')

    def update_timer(self):
        timer_tpl = self.get_config_tpl_data('TIMER')
        timer_tpl['core'] = self.gen_core(self.start_core)
        self.update_write_parser(timer_tpl)
        self.start_core += 1

    def get_config_tpl_data(self, type_value):
        for section in self.read_parser.sections():
            if self.read_parser.has_option(section, 'type'):
                if type_value == self.read_parser.get(section, 'type'):
                    tpl = OrderedDict(self.read_parser.items(section))
                    return tpl

    def get_txrx_tpl_data(self, value):
        for section in self.read_parser.sections():
            if self.read_parser.has_option(section, 'pipeline_txrx_type'):
                if value == self.read_parser.get(section, 'pipeline_txrx_type'):
                    tpl = OrderedDict(self.read_parser.items(section))
                    return tpl

    def init_write_parser_template(self, type_value='ARPICMP'):
        for section in self.read_parser.sections():
            if type_value == self.parser_get(self.read_parser, section, 'type', object()):
                self.start_core = self.read_parser.getint(section, 'core')
                self.pipeline_counter = self.read_parser.getint(section, 'core')
                self.txrx_pipeline = self.read_parser.getint(section, 'core')
                return
            self.write_parser.add_section(section)
            for name, value in self.read_parser.items(section):
                self.write_parser.set(section, name, value)

    def update_write_parser(self, data):
        section = "PIPELINE{0}".format(self.pipeline_counter)
        self.write_parser.add_section(section)
        for name, value in data.items():
            self.write_parser.set(section, name, value)

    def get_worker_threads(self, worker_threads):
        if self.worker_config == '1t':
            return worker_threads
        else:
            return worker_threads - worker_threads % 2

    def generate_next_core_id(self):
        if self.worker_config == '1t':
            self.start_core += 1
            return

        try:
            self.start_core = '{}h'.format(int(self.start_core))
        except ValueError:
            self.start_core = int(self.start_core[:-1]) + 1

    @staticmethod
    def get_port_pairs(interfaces):
        port_pair_list = []
        networks = defaultdict(list)
        for private_intf in interfaces:
            vintf = private_intf['virtual-interface']
            networks[vintf['vld_id']].append(vintf)

        for name, net in networks.items():
            # partition returns a tuple
            parts = list(name.partition('private'))
            if parts[0]:
                # 'private' was not in or not leftmost in the string
                continue
            parts[1] = 'public'
            public_id = ''.join(parts)
            for private_intf in net:
                try:
                    public_peer_intfs = networks[public_id]
                except KeyError:
                    LOG.warning("private network without peer %s, %s not found", name, public_id)
                    continue

                for public_intf in public_peer_intfs:
                    port_pair = private_intf["ifname"], public_intf["ifname"]
                    port_pair_list.append(port_pair)

        return port_pair_list, networks

    def get_lb_count(self):
        self.lb_count = int(min(len(self.port_pair_list), self.lb_count))

    def generate_lb_to_port_pair_mapping(self):
        self.lb_to_port_pair_mapping = defaultdict(int)
        port_pair_count = len(self.port_pair_list)
        lb_pair_count = int(port_pair_count / self.lb_count)
        for i in range(self.lb_count):
            self.lb_to_port_pair_mapping[i + 1] = lb_pair_count
        for i in range(port_pair_count % self.lb_count):
            self.lb_to_port_pair_mapping[i + 1] += 1

    def set_priv_to_pub_mapping(self):
        return "".join(str(y) for y in [(int(x[0][-1]), int(x[1][-1])) for x in
                                        self.port_pair_list])

    def set_priv_que_handler(self):
        # iterated twice, can't be generator
        priv_to_pub_map = [(int(x[0][-1]), int(x[1][-1])) for x in self.port_pairs]
        # must be list to use .index()
        port_list = list(chain.from_iterable(priv_to_pub_map))
        priv_ports = (x[0] for x in priv_to_pub_map)
        self.prv_que_handler = '({})'.format(
            ",".join((str(port_list.index(x)) for x in priv_ports)))

    def generate_arp_route_tbl(self):
        arp_config = []
        arp_route_tbl_tmpl = "({port0_dst_ip_hex},{port0_netmask_hex},{port_num}," \
                             "{next_hop_ip_hex})"
        for port_pair in self.port_pair_list:
            for port in port_pair:
                port_num = int(port[-1])
                interface = self.interfaces[port_num]
                # We must use the dst because we are on the VNF and we need to
                # reach the TG.
                dst_port0_ip = \
                    ipaddress.ip_interface(six.text_type(
                        "%s/%s" % (interface["virtual-interface"]["dst_ip"],
                                   interface["virtual-interface"]["netmask"])))
                arp_vars = {
                    "port0_dst_ip_hex": ip_to_hex(dst_port0_ip.network.network_address.exploded),
                    "port0_netmask_hex": ip_to_hex(dst_port0_ip.network.netmask.exploded),
                    # this is the port num that contains port0 subnet and next_hop_ip_hex
                    "port_num": port_num,
                    # next hop is dst in this case
                    # must be within subnet
                    "next_hop_ip_hex": ip_to_hex(dst_port0_ip.ip.exploded),
                }
                arp_config.append(arp_route_tbl_tmpl.format(**arp_vars))

        return ' '.join(arp_config)

    def generate_arpicmp_data(self):
        swq_in_str = self.make_range_str('SWQ{}', self.swq, offset=self.lb_count)
        self.swq += self.lb_count
        swq_out_str = self.make_range_str('SWQ{}', self.swq, offset=self.lb_count)
        self.swq += self.lb_count
        # ports_mac_list is disabled for some reason
        # mac_iter = (self.interfaces[int(x[-1])]['virtual-interface']['local_mac']
        #             for port_pair in self.port_pair_list for x in port_pair)
        pktq_in_iter = ('RXQ{}'.format(float(x[0][-1])) for x in self.port_pair_list)

        arpicmp_data = {
            'core': self.gen_core(self.start_core),
            'pktq_in': swq_in_str,
            'pktq_out': swq_out_str,
            # we need to disable ports_mac_list?
            # it looks like ports_mac_list is no longer required
            # 'ports_mac_list': ' '.join(mac_iter),
            'pktq_in_prv': ' '.join(pktq_in_iter),
            'prv_to_pub_map': self.set_priv_to_pub_mapping(),
            'arp_route_tbl': self.generate_arp_route_tbl(),
            # nd_route_tbl must be set or we get segault on random OpenStack IPv6 traffic
            # 'nd_route_tbl': "(0064:ff9b:0:0:0:0:9810:6414,120,0,0064:ff9b:0:0:0:0:9810:6414)"
            # safe default?  route discard prefix to localhost
            'nd_route_tbl': "(0100::,64,0,::1)"
        }
        self.pktq_out_os = swq_out_str.split(' ')
        # HWLB is a run to complition. So override the pktq_in/pktq_out
        if self.lb_config == self.HW_LB:
            self.swq = 0
            swq_in_str = \
                self.make_range_str('SWQ{}', self.swq,
                                    offset=(self.lb_count * self.worker_threads))
            arpicmp_data['pktq_in'] = swq_in_str
            # WA: Since port_pairs will not be populated during arp pipeline
            self.port_pairs = self.port_pair_list
            port_iter = \
                self.make_port_pairs_iter(self.float_x_plus_one_tenth_of_y, [self.mul])
            pktq_out = self.make_str('TXQ{}', port_iter)
            arpicmp_data['pktq_out'] = pktq_out

        return arpicmp_data

    def generate_final_txrx_data(self):
        swq_start = self.swq - self.ports_len * self.worker_threads

        txq_start = 0
        txq_end = self.worker_threads

        pktq_out_iter = self.make_range_port_pairs_iter(self.float_x_plus_one_tenth_of_y,
                                                        txq_start, txq_end)

        swq_str = self.make_range_str('SWQ{}', swq_start, self.swq)
        txq_str = self.make_str('TXQ{}', pktq_out_iter)
        rxtx_data = {
            'pktq_in': swq_str,
            'pktq_out': txq_str,
            'pipeline_txrx_type': 'TXTX',
            'core': self.gen_core(self.start_core),
        }
        pktq_in = rxtx_data['pktq_in']
        pktq_in = '{0} {1}'.format(pktq_in, self.pktq_out_os[self.lb_index - 1])
        rxtx_data['pktq_in'] = pktq_in
        self.pipeline_counter += 1
        return rxtx_data

    def generate_initial_txrx_data(self):
        pktq_iter = self.make_range_port_pairs_iter(self.float_x_plus_one_tenth_of_y,
                                                    0, self.worker_threads)

        rxq_str = self.make_str('RXQ{}', pktq_iter)
        swq_str = self.make_range_str('SWQ{}', self.swq, offset=self.ports_len)
        txrx_data = {
            'pktq_in': rxq_str,
            'pktq_out': swq_str + ' SWQ{0}'.format(self.lb_index - 1),
            'pipeline_txrx_type': 'RXRX',
            'core': self.gen_core(self.start_core),
        }
        self.pipeline_counter += 1
        return txrx_data

    def generate_lb_data(self):
        pktq_in = self.make_range_str('SWQ{}', self.swq, offset=self.ports_len)
        self.swq += self.ports_len

        offset = self.ports_len * self.worker_threads
        pktq_out = self.make_range_str('SWQ{}', self.swq, offset=offset)
        self.pktq_out = pktq_out.split()

        self.swq += (self.ports_len * self.worker_threads)
        lb_data = {
            'prv_que_handler': self.prv_que_handler,
            'pktq_in': pktq_in,
            'pktq_out': pktq_out,
            'n_vnf_threads': str(self.worker_threads),
            'core': self.gen_core(self.start_core),
        }
        self.pipeline_counter += 1
        return lb_data

    def generate_vnf_data(self):
        if self.lb_config == self.HW_LB:
            port_iter = self.make_port_pairs_iter(self.float_x_plus_one_tenth_of_y, [self.mul])
            pktq_in = self.make_str('RXQ{}', port_iter)

            self.mul += 1
            port_iter = self.make_port_pairs_iter(self.float_x_plus_one_tenth_of_y, [self.mul])
            pktq_out = self.make_str('TXQ{}', port_iter)

            pipe_line_data = {
                'pktq_in': pktq_in,
                'pktq_out': pktq_out + ' SWQ{0}'.format(self.swq),
                'prv_que_handler': self.prv_que_handler,
                'core': self.gen_core(self.start_core),
            }
            self.swq += 1
        else:
            pipe_line_data = {
                'pktq_in': ' '.join((self.pktq_out.pop(0) for _ in range(self.ports_len))),
                'pktq_out': self.make_range_str('SWQ{}', self.swq, offset=self.ports_len),
                'prv_que_handler': self.prv_que_handler,
                'core': self.gen_core(self.start_core),
            }
            self.swq += self.ports_len

        if self.vnf_type in ('ACL', 'VFW'):
            pipe_line_data.pop('prv_que_handler')

        if self.vnf_tpl.get('vnf_set'):
            public_ip_port_range_list = self.vnf_tpl['public_ip_port_range'].split(':')
            ip_in_hex = '{:x}'.format(int(public_ip_port_range_list[0], 16) + self.lb_index - 1)
            public_ip_port_range_list[0] = ip_in_hex
            self.vnf_tpl['public_ip_port_range'] = ':'.join(public_ip_port_range_list)

        self.pipeline_counter += 1
        return pipe_line_data

    def generate_config_data(self):
        self.init_write_parser_template()

        # use master core for master, don't use self.start_core
        self.write_parser.set('PIPELINE0', 'core', self.gen_core(self.master_core))
        arpicmp_data = self.generate_arpicmp_data()
        self.arpicmp_tpl.update(arpicmp_data)
        self.update_write_parser(self.arpicmp_tpl)

        self.start_core += 1
        if self.vnf_type == 'CGNAPT':
            self.pipeline_counter += 1
            self.update_timer()

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
            if self.lb_config == 'SW':
                txrx_data = self.generate_initial_txrx_data()
                self.txrx_tpl.update(txrx_data)
                self.update_write_parser(self.txrx_tpl)
                self.start_core += 1
                lb_data = self.generate_lb_data()
                self.loadb_tpl.update(lb_data)
                self.update_write_parser(self.loadb_tpl)
                self.start_core += 1

            for i in range(self.worker_threads):
                vnf_data = self.generate_vnf_data()
                if not self.vnf_tpl:
                    self.vnf_tpl = {}
                self.vnf_tpl.update(vnf_data)
                self.update_write_parser(self.vnf_tpl)
                try:
                    self.vnf_tpl.pop('vnf_set')
                except KeyError:
                    pass
                else:
                    self.vnf_tpl.pop('public_ip_port_range')
                self.generate_next_core_id()

            if self.lb_config == 'SW':
                txrx_data = self.generate_final_txrx_data()
                self.txrx_tpl.update(txrx_data)
                self.update_write_parser(self.txrx_tpl)
                self.start_core += 1
            self.vnf_tpl = self.get_config_tpl_data(self.vnf_type)

    def generate_config(self):
        self.port_pair_list, self.networks = self.get_port_pairs(self.interfaces)
        self.get_lb_count()
        self.generate_lb_to_port_pair_mapping()
        self.generate_config_data()
        self.write_parser.write(sys.stdout)
        with open(self.tmp_file, 'a') as tfh:
            self.write_parser.write(tfh)

    def generate_link_config(self):

        link_configs = []
        for port_pair in self.port_pair_list:
            for port in port_pair:
                port = port[-1]
                virtual_interface = self.interfaces[int(port)]["virtual-interface"]
                local_ip = virtual_interface["local_ip"]
                netmask = virtual_interface["netmask"]
                port_ip, prefix_len = self.validate_ip_and_prefixlen(local_ip, netmask)
                link_configs.append(LINK_CONFIG_TEMPLATE.format(port, port_ip, prefix_len))

        return ''.join(link_configs)

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
        for port_pair in self.port_pair_list:
            for port in port_pair:
                # ignore gateway, always use TG IP
                # gateway = self.get_ports_gateway(port)
                dst_mac = self.interfaces[int(port[-1])]["virtual-interface"]["dst_mac"]
                dst_ip = self.interfaces[int(port[-1])]["virtual-interface"]["dst_ip"]
                # arp_config.append((port[-1], gateway, dst_mac, self.txrx_pipeline))
                # so dst_mac is the TG dest mac, so we need TG dest IP.
                arp_config.append((port[-1], dst_ip, dst_mac, self.txrx_pipeline))

        return '\n'.join(('p {3} arpadd {0} {1} {2}'.format(*values) for values in arp_config))

    def generate_arp_config6(self):
        arp_config6 = []
        for port_pair in self.port_pair_list:
            for port in port_pair:
                # ignore gateway, always use TG IP
                # gateway6 = self.get_ports_gateway6(port)
                dst_mac6 = self.interfaces[int(port[-1])]["virtual-interface"]["dst_mac"]
                dst_ip6 = self.interfaces[int(port[-1])]["virtual-interface"]["dst_ip"]
                # arp_config6.append((port[-1], gateway6, dst_mac6, self.txrx_pipeline))
                arp_config6.append((port[-1], dst_ip6, dst_mac6, self.txrx_pipeline))

        return '\n'.join(('p {3} arpadd {0} {1} {2}'.format(*values) for values in arp_config6))

    def generate_action_config(self):
        port_list = []
        for port_pair in self.port_pair_list:
            for port in port_pair:
                port_list.append(port[-1])

        if self.vnf_type == "VFW":
            template = FW_ACTION_TEMPLATE
        else:
            template = ACTION_TEMPLATE

        return ''.join((template.format(port) for port in port_list))

    def get_ip_from_port(self, port):
        # we can't use gateway because in OpenStack gateways interfer with floating ip routing
        # return self.make_ip_addr(self.get_ports_gateway(port), self.get_netmask_gateway(port))
        ip = self.interfaces[port]["virtual-interface"]["local_ip"]
        netmask = self.interfaces[port]["virtual-interface"]["netmask"]
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
        pattern = 'p {0} add {1} {2} {3} {4} {5} 0 65535 0 65535 0 0 {6}'
        for port_pair in self.port_pair_list:
            src_port = int(port_pair[0][-1])
            dst_port = int(port_pair[1][-1])

            src_net, src_prefix_len = self.get_network_and_prefixlen_from_ip_of_port(src_port)
            dst_net, dst_prefix_len = self.get_network_and_prefixlen_from_ip_of_port(dst_port)
            # ignore entires with empty values
            if all((src_net, src_prefix_len, dst_net, dst_prefix_len)):
                new_rules.append((cmd, self.txrx_pipeline, src_net, src_prefix_len,
                                  dst_net, dst_prefix_len, dst_port))
                new_rules.append((cmd, self.txrx_pipeline, dst_net, dst_prefix_len,
                                  src_net, src_prefix_len, src_port))

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
        new_rules_config = '\n'.join(pattern.format(*values) for values
                                     in chain(new_rules, new_ipv6_rules))
        return ''.join([rules_config, new_rules_config, acl_apply])

    def generate_script_data(self):
        self.port_pair_list, self.networks = self.get_port_pairs(self.interfaces)
        self.get_lb_count()
        script_data = {
            'link_config': self.generate_link_config(),
            'arp_config': self.generate_arp_config(),
            # disable IPv6 for now
            # 'arp_config6': self.generate_arp_config6(),
            'arp_config6': "",
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
                script += hwlb_tpl.format(port_pair[0][-1], port_pair[1][-1])
        return script
