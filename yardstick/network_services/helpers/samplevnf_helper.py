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
import logging
import yaml
import ipaddress
import os
import six
import subprocess
import time
import posixpath
import itertools
import sys
from six.moves.configparser import SafeConfigParser
from collections import OrderedDict

log = logging.getLogger(__name__)

SAMPLE_VNF_REPO = 'https://gerrit.opnfv.org/gerrit/samplevnf'
REPO_NAME = posixpath.basename(SAMPLE_VNF_REPO)
SAMPLE_REPO_DIR = os.path.join('~/', REPO_NAME)

LOG = logging.getLogger(__name__)

# This sets up a basic passthrough with no rules
SCRIPT_TPL = """
{link_config}

{arp_config}

{arp_config6}

{actions}

{rules}

"""


class OPNFVSampleVNF(object):

    def __init__(self, connection, bin_path):
        super(OPNFVSampleVNF, self).__init__()
        self.connection = connection
        self.bin_path = bin_path

    def deploy_vnfs(self, vnf_name):
        vnf_bin = os.path.join(self.bin_path, vnf_name)
        exit_status = self.connection.execute("which %s" % vnf_bin)[0]
        if exit_status:
            subprocess.check_output(["rm", "-rf", REPO_NAME])
            subprocess.check_output(["git", "clone", SAMPLE_VNF_REPO])
            time.sleep(2)
            self.connection.execute("rm -rf %s" % SAMPLE_REPO_DIR)
            self.connection.put(REPO_NAME, SAMPLE_REPO_DIR, True)

            build_script = os.path.join(SAMPLE_REPO_DIR, 'tools/vnf_build.sh')
            time.sleep(2)
            http_proxy = os.environ.get('http_proxy', '')
            https_proxy = os.environ.get('https_proxy', '')
            LOG.debug("sudo -E %s --silient '%s' '%s'" %
                      (build_script, http_proxy, https_proxy))
            self.connection.execute("sudo -E %s --silient '%s' '%s'" %
                                    (build_script, http_proxy,
                                     https_proxy))
            vnf_bin_loc = os.path.join(SAMPLE_REPO_DIR, "VNFs/%s/build/%s" %
                                       (vnf_name, vnf_name))
            self.connection.execute("sudo mkdir -p %s" % (self.bin_path))
            self.connection.execute("sudo cp %s %s" % (vnf_bin_loc, vnf_bin))


class MultiPortConfig(object):
    def __init__(
            self, topology_file, config_tpl, tmp_file, interfaces={},
            vnf_type='CGNAT', lb_count=2, worker_threads=3,
            worker_config='1C/1T', lb_config='SW', socket=0):

        super(MultiPortConfig, self).__init__()
        self.topology_file = topology_file
        self.worker_config = worker_config.split('/')[1].lower()
        self.worker_threads = self.get_worker_threads(worker_threads)
        self.vnf_type = vnf_type
        self.pipe_line = 0
        self.interfaces = interfaces
        self.write_parser = SafeConfigParser()
        self.read_parser = SafeConfigParser()
        if not os.path.isfile(config_tpl):
            config_tpl = self.get_absolute_path(config_tpl)
        self.read_parser.read(config_tpl)
        self.master_tpl = self.get_config_tpl_data('MASTER')
        self.arpicmp_tpl = self.get_config_tpl_data('ARPICMP')
        self.txrx_tpl = self.get_config_tpl_data('TXRX')
        self.loadb_tpl = self.get_config_tpl_data('LOADB')
        self.vnf_tpl = self.get_config_tpl_data(vnf_type)
        self.swq = 0
        self.lb_count = lb_count
        self.lb_config = lb_config
        self.tmp_file = "/tmp/{0}".format(tmp_file)
        self.pktq_out_os = []
        self.socket = socket
        self.init_eal()

    def init_eal(self):
        vpci = [v['virtual-interface']["vpci"] for v in self.interfaces]
        with open(self.tmp_file, 'w') as fh:
            fh.write('[EAL]\n')
            for item in vpci:
                fh.write('w = {0}\n'.format(item))
            fh.write('\n')

    def update_timer(self):
        timer_tpl = self.get_config_tpl_data('TIMER')
        timer_data = {
            'core': "s" + str(self.socket) + "c" + str(self.start_core)
        }
        timer_tpl.update(timer_data)
        self.update_write_parser(timer_tpl)
        self.start_core += 1

    def get_absolute_path(self, file_name):
        try:
            cwd = os.getcwd()
            cwd_list = cwd.split('/')
            nsut_index = cwd_list.index('nsut')
            cwd_list[nsut_index + 2:] = []
            vnf_path = '/'.join(cwd_list)
            config_tpl_path = os.path.join(vnf_path, file_name)
            return config_tpl_path
        except ValueError:
            raise

    def get_config_tpl_data(self, type_value):
        for section in self.read_parser.sections():
            if self.read_parser.has_option(section, 'type'):
                if type_value == self.read_parser.get(section, 'type'):
                    tpl = OrderedDict(self.read_parser.items(section))
                    return tpl

    def get_txrx_tpl_data(self, value):
        for section in self.read_parser.sections():
            if self.read_parser.has_option(section, 'pipeline_txrx_type'):
                if value == self.read_parser.get(
                        section, 'pipeline_txrx_type'):
                    tpl = OrderedDict(self.read_parser.items(section))
                    return tpl

    def init_write_parser_template(self, type_value='ARPICMP'):
        for section in self.read_parser.sections():
            if self.read_parser.has_option(section, 'type'):
                if type_value == self.read_parser.get(section, 'type'):
                    self.start_core = self.read_parser.getint(
                        section, 'core')
                    self.pipeline_counter = self.read_parser.getint(
                        section, 'core')
                    self.txrx_pipeline = self.read_parser.getint(
                        section, 'core')
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
            if worker_threads % 2 == 0:
                return worker_threads
            else:
                return worker_threads - 1

    def generate_next_core_id(self):
        if self.worker_config == '1t':
            self.start_core += 1
        else:
            try:
                core = int(self.start_core)
                core = str(core) + 'h'
            except ValueError:
                core = int(self.start_core[:-1]) + 1
            self.start_core = core

    def get_port_pairs(self):
        with open(self.topology_file) as fh:
            yaml_data = yaml.safe_load(fh.read())
        self.port_pair_list = []
        for ele in yaml_data['nsd:nsd-catalog']['nsd'][0]['vld']:
            if ele['id'].startswith('private'):
                private_id = ele['id']
                private_data = ele['vnfd-connection-point-ref']
                public_id = ('public' if private_id == 'private' else
                             'public_' + private_id.split('_')[1])
                public_data = ([ele['vnfd-connection-point-ref'] for ele in
                               yaml_data['nsd:nsd-catalog']['nsd'][0]['vld'] if
                               ele['id'] == public_id][0])
                priv_ref_ids = [data['vnfd-id-ref'] for data in private_data]
                pub_ref_ids = [data['vnfd-id-ref'] for data in public_data]
                vnf_ref_id = next(iter(set(priv_ref_ids).intersection(
                    pub_ref_ids)))
                private_data.extend(public_data)
                port_pair = (tuple(data['vnfd-connection-point-ref'] for
                             data in private_data if
                             data['vnfd-id-ref'] == vnf_ref_id))
                self.port_pair_list.append(port_pair)
        if len(self.port_pair_list) < self.lb_count:
            self.lb_count = len(self.port_pair_list)

    def generate_lb_to_port_pair_mapping(self):
        self.lb_to_port_pair_mapping = {}
        port_pair_count = len(self.port_pair_list) / self.lb_count
        for i in range(self.lb_count):
            self.lb_to_port_pair_mapping[i + 1] = port_pair_count
        for i in range(len(self.port_pair_list) % self.lb_count):
            self.lb_to_port_pair_mapping[i + 1] = (
                self.lb_to_port_pair_mapping.get(i + 1, 0) + 1)

    def set_priv_to_pub_mapping(self):
        return "".join(str(y) for y in [(int(x[0][-1]), int(x[1][-1])) for x in
                       self.port_pair_list])

    def set_priv_que_handler(self):
        priv_to_pub_map = [(int(x[0][-1]), int(x[1][-1])) for x in
                           self.port_pairs]
        port_list = list(itertools.chain(*priv_to_pub_map))
        priv_ports = [x[0] for x in priv_to_pub_map]
        self.prv_que_handler = str(tuple([port_list.index(x) for x in
                                   priv_ports]))

    def generate_arpicmp_data(self):
        arpicmp_data = {
            'core': "s" + str(self.socket) + "c" + str(self.start_core),
            'pktq_in': ' '.join(['SWQ' + str(x) for x in range(
                self.swq, self.swq + self.lb_count)]),
            'pktq_out': ' '.join(['TXQ' + str(float(x[-1])) for x in
                                 itertools.chain(*self.port_pair_list)]),
            'ports_mac_list': ' '.join(
                [self.interfaces[int(
                    x[-1])]['virtual-interface']['local_mac'] for
                    port_pair in self.port_pair_list for x in port_pair]),
            'pktq_in_prv': ' '.join(
                ['RXQ' + str(float(x[0][-1])) for x in self.port_pair_list]),
            'prv_to_pub_map': self.set_priv_to_pub_mapping()}
        arpicmp_data['pktq_out'] = ' '.join(['SWQ' + str(x) for x in range(
            self.swq, self.swq + self.lb_count)])
        self.swq += self.lb_count
        self.pktq_out_os = arpicmp_data['pktq_out'].split(' ')
        if self.lb_config == "HW":
            arpicmp_data['pktq_in'] = ' '.join(
                ['SWQ' + str(x) for x in range(0, (
                    self.lb_count * self.worker_threads))])
            self.swq = 0
        return arpicmp_data

    def generate_final_txrx_data(self):
        start = 0
        end = self.worker_threads
        pktq_out = [float(x[-1]) + float(0.1 * i) for i in range(
            start, end) for x in list(
            itertools.chain(*self.port_pairs))]
        rxtx_data = {
            'pktq_in': ' '.join(['SWQ' + str(x) for x in range(
                self.swq - (
                    self.ports_len * self.worker_threads), self.swq)]),
            'pktq_out': ' '.join(['TXQ' + str(x) for x in pktq_out]),
            'pipeline_txrx_type': 'TXTX',
            'core': "s" + str(self.socket) + "c" + str(self.start_core)
        }
        pktq_in = rxtx_data['pktq_in']
        pktq_in = \
            '{0} {1}'.format(pktq_in, self.pktq_out_os[self.lb_index - 1])
        rxtx_data['pktq_in'] = pktq_in
        self.pipeline_counter += 1
        return rxtx_data

    def generate_initial_txrx_data(self):
        pktq = [float(x[-1]) + float(0.1 * i) for i in range(
            0, self.worker_threads) for x in list(
            itertools.chain(*self.port_pairs))]
        txrx_data = {
            'pktq_in': ' '.join(['RXQ' + str(x) for x in pktq]),
            'pktq_out': ' '.join(['SWQ' + str(x) for x in range(
                self.swq, self.swq + self.ports_len)]) + ' SWQ{0}'.format(
                self.lb_index - 1),
            'pipeline_txrx_type': 'RXRX',
            'core': "s" + str(self.socket) + "c" + str(self.start_core)
        }
        self.pipeline_counter += 1
        return txrx_data

    def generate_lb_data(self):
        pktq_in = ' '.join(['SWQ' + str(x) for x in range(
            self.swq, self.swq + self.ports_len)])
        self.swq += self.ports_len
        pktq_out = ' '.join(['SWQ' + str(x) for x in range(
            self.swq, self.swq + (self.ports_len * self.worker_threads))])
        self.pktq_out = pktq_out.split()
        self.swq += (self.ports_len * self.worker_threads)
        lb_data = {
            'prv_que_handler': self.prv_que_handler,
            'pktq_in': pktq_in,
            'pktq_out': pktq_out,
            'n_vnf_threads': str(self.worker_threads),
            'core': "s" + str(self.socket) + "c" + str(self.start_core)
        }
        self.pipeline_counter += 1
        return lb_data

    def generate_vnf_data(self):
        if self.lb_config == 'HW':
            pktq_in = [float(x[-1]) + float(0.1 * self.mul) for x in list(
                itertools.chain(*self.port_pairs))]
            self.mul += 1
            pktq_out = [float(x[-1]) + float(0.1 * self.mul) for x in list(
                itertools.chain(*self.port_pairs))]
            pipe_line_data = {
                'pktq_in': ' '.join(['RXQ' + str(x) for x in pktq_in]),
                'pktq_out': (' '.join(['TXQ' + str(x) for x in pktq_out]) +
                             ' SWQ{0}'.format(self.swq)),
                'prv_que_handler': self.prv_que_handler,
                'core': "s" + str(self.socket) + "c" + str(self.start_core)
            }
            self.swq += 1
        else:
            pipe_line_data = {
                'pktq_in': ' '.join([self.pktq_out.pop(0) for i in range(
                    self.ports_len)]),
                'pktq_out': ' '.join(['SWQ' + str(x) for x in range(
                    self.swq, self.swq + self.ports_len)]),
                'prv_que_handler': self.prv_que_handler,
                'core': "s" + str(self.socket) + "c" + str(self.start_core)
            }
            self.swq += self.ports_len
        if self.vnf_type in ('ACL', 'VFW'):
            pipe_line_data.pop('prv_que_handler')
        if self.vnf_tpl.get('vnf_set', None):
            public_ip_port_range = self.vnf_tpl['public_ip_port_range']
            public_ip_port_range = public_ip_port_range.split(':')
            ip_in_hex = public_ip_port_range[0]
            ip_in_hex = format(int(ip_in_hex, 16) + self.lb_index - 1, 'x')
            public_ip_port_range[0] = ip_in_hex
            self.vnf_tpl['public_ip_port_range'] = ':'.join(
                public_ip_port_range)
        self.pipeline_counter += 1
        return pipe_line_data

    def generate_config_data(self):
        self.init_write_parser_template()

        self.write_parser.set(
            'PIPELINE0', 'core',
            "s" + str(self.socket) + "c" + str(self.start_core))
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
            self.port_pairs = [self.port_pair_list.pop(0) for i in range(
                port_pair_count)]
            self.ports_len = len(self.port_pairs) * 2
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
                if self.vnf_tpl.get('vnf_set', None):
                    self.vnf_tpl.pop('vnf_set')
                    self.vnf_tpl.pop('public_ip_port_range')
                self.generate_next_core_id()
            if self.lb_config == 'SW':
                txrx_data = self.generate_final_txrx_data()
                self.txrx_tpl.update(txrx_data)
                self.update_write_parser(self.txrx_tpl)
                self.start_core += 1
            self.vnf_tpl = self.get_config_tpl_data(self.vnf_type)

    def generate_config(self):
        self.get_port_pairs()
        self.generate_lb_to_port_pair_mapping()
        self.generate_config_data()
        self.write_parser.write(sys.stdout)
        with open(self.tmp_file, 'a') as tfh:
            self.write_parser.write(tfh)

    def generate_link_config(self):
        link_config = ""
        for port_pair in self.port_pair_list:
            for port in port_pair:
                port_ip = ipaddress.ip_interface(six.text_type("%s/%s" % (
                    self.interfaces[int(
                        port[-1])]["virtual-interface"]["local_ip"],
                    self.interfaces[int(
                        port[-1])]["virtual-interface"][
                        "netmask"]))).ip.exploded
                prefix_len = ipaddress.ip_interface(six.text_type("%s/%s" % (
                    self.interfaces[int(
                        port[-1])]["virtual-interface"]["local_ip"],
                    self.interfaces[int(
                        port[-1])]["virtual-interface"][
                        "netmask"]))).network.prefixlen
                link_config += "link {0} down\n".format(port[-1])
                link_config += "link {0} config {1} {2}\n".format(
                    port[-1], port_ip, prefix_len)
                link_config += "link {0} up\n".format(port[-1])
        return link_config

    def get_ports_gateway(self, port):
        if 'routing_table' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['routing_table']
            return next((route['gateway'] for route in routing_table if
                         route['if'] == port), None)

    def get_ports_gateway6(self, port):
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            nd_route_tbl = self.vnfd['vdu'][0]['nd_route_tbl']
            return next((route['gateway'] for route in nd_route_tbl if
                         route['if'] == port), None)

    def get_netmask_gateway(self, port):
        if 'routing_table' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['routing_table']
            return next((route['netmask'] for route in routing_table if
                         route['if'] == port), None)

    def get_netmask_gateway6(self, port):
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            nd_route_tbl = self.vnfd['vdu'][0]['nd_route_tbl']
            return next((route['netmask'] for route in nd_route_tbl if
                         route['if'] == port), None)

    def generate_arp_config(self):
        arp_config = ''
        for port_pair in self.port_pair_list:
            for port in port_pair:
                gateway = self.get_ports_gateway(port)
                dst_mac = self.interfaces[int(
                    port[-1])]["virtual-interface"]["dst_mac"]
                arp_config += 'p {3} arpadd {0} {1} {2}\n'.format(
                    port[-1], gateway, dst_mac, self.txrx_pipeline)
        return arp_config

    def generate_arp_config6(self):
        arp_config6 = ''
        for port_pair in self.port_pair_list:
            for port in port_pair:
                gateway6 = self.get_ports_gateway6(port)
                dst_mac6 = self.interfaces[int(
                    port[-1])]["virtual-interface"]["dst_mac"]
                arp_config6 += 'p {3} arpadd {0} {1} {2}\n'.format(
                    port[-1], gateway6, dst_mac6, self.txrx_pipeline)
        return arp_config6

    def generate_action_config(self):
        action_config = ''
        port_list = []
        for port_pair in self.port_pair_list:
            for port in port_pair:
                port = port[-1]
                port_list.append(port)
                action = "p action add {0} accept\n".format(port)
                action += "p action add {0} fwd {0}\n".format(port)
                action += "p action add {0} count\n".format(port)
                action_config += action
        if self.vnf_type == "VFW":
            for port in port_list:
                action_config += "p action add {0} conntrack\n".format(port)
        return action_config

    def generate_rule_config(self):
        cmd = 'acl' if self.vnf_type == "ACL" else "vfw"
        rules_config = self.rules if self.rules else ''
        rules_config_ipv6 = ''
        for port_pair in self.port_pair_list:
            src_port = int(port_pair[0][-1])
            dst_port = int(port_pair[1][-1])

            pattern = '\np {0} add {1} {2} {3} {4} {5} 0 65535 0 65535 0 0 {6}'
            src_ip = self.get_ports_gateway(port_pair[0])
            src_prefix_len = self.get_netmask_gateway(port_pair[0])
            src_prefix_len = \
                ipaddress.ip_interface(six.text_type(
                    "%s/%s" % (src_ip, src_prefix_len))).network.prefixlen
            dst_ip = self.get_ports_gateway(port_pair[1])
            dst_prefix_len = self.get_netmask_gateway(port_pair[0])
            dst_prefix_len = ipaddress.ip_interface(six.text_type(
                "%s/%s" % (dst_ip, dst_prefix_len))).network.prefixlen
            rule = pattern.format(
                cmd, self.txrx_pipeline, src_ip, src_prefix_len,
                dst_ip, dst_prefix_len, dst_port)
            rule += pattern.format(
                cmd, self.txrx_pipeline, dst_ip, dst_prefix_len,
                src_ip, src_prefix_len, src_port)
            rules_config += rule

            src_ip = self.get_ports_gateway6(port_pair[0])
            src_prefix_len = self.get_netmask_gateway6(port_pair[0])
            dst_ip = self.get_ports_gateway6(port_pair[1])
            dst_prefix_len = self.get_netmask_gateway6(port_pair[0])
            rule = pattern.format(
                cmd, self.txrx_pipeline, src_ip, src_prefix_len,
                dst_ip, dst_prefix_len, dst_port)
            rule += pattern.format(
                cmd, self.txrx_pipeline, dst_ip, dst_prefix_len,
                src_ip, src_prefix_len, src_port)
            rules_config_ipv6 += rule

        acl_apply = "\np %s applyruleset" % cmd
        return rules_config + rules_config_ipv6 + acl_apply

    def generate_script_data(self):
        script_data = {}
        self.get_port_pairs()
        script_data['link_config'] = self.generate_link_config()
        script_data['arp_config'] = self.generate_arp_config()
        script_data['arp_config6'] = self.generate_arp_config6()
        script_data['actions'] = ''
        script_data['rules'] = ''
        if self.vnf_type in ('ACL', 'VFW'):
            script_data['actions'] = self.generate_action_config()
            script_data['rules'] = self.generate_rule_config()
        return script_data

    def generate_script(self, vnfd, rules=None):
        self.vnfd = vnfd
        self.rules = rules
        script_data = self.generate_script_data()
        script = SCRIPT_TPL.format(**script_data)
        if self.lb_config == 'HW':
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
