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
""" vPE (Power Edge router) VNF model definitions based on IETS Spec """

from __future__ import absolute_import
from __future__ import print_function
import tempfile
import time
import os
import logging
import re
from multiprocessing import Queue
import multiprocessing
import ipaddress
import yaml
import itertools
import six.moves.configparser
import six

from yardstick import ssh
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.utils import provision_tool
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.nfvi.resource import ResourceProfile
from six.moves import range

LOG = logging.getLogger(__name__)
VPE_PIPELINE_COMMAND = \
    'sudo {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'
CORES = ['0', '1', '2', '3', '4', '5']
WAIT_TIME = 20


class ConfigCreate(object):
    def __init__(self, priv_ports, pub_ports, socket):
        super(ConfigCreate, self).__init__()
        self.sw_q = -1
        self.sink_q = -1
        self.n_pipeline = 1
        self.priv_ports = priv_ports
        self.pub_ports = pub_ports
        self.pipeline_per_port = 9
        self.socket = socket

    def vpe_initialize(self, Config):
        Config.add_section('EAL')
        Config.set('EAL', 'log_level', '0')

        Config.add_section('PIPELINE0')
        Config.set('PIPELINE0', 'type', 'MASTER')
        Config.set('PIPELINE0', 'core', 'S%sC0' % self.socket)

        Config.add_section('MEMPOOL0')
        Config.set('MEMPOOL0', 'pool_size', '256K')

        Config.add_section('MEMPOOL1')
        Config.set('MEMPOOL1', 'pool_size', '2M')
        return Config

    def vpe_rxq(self, Config):
        for ports in self.pub_ports:
            Config.add_section('RXQ%s.0' % str(ports))
            Config.set('RXQ%s.0' % str(ports), 'mempool', 'MEMPOOL1')

        return Config

    def vpe_tmq(self, Config, index):
        tm_q = 'TM%s' % str(index)
        Config.add_section(tm_q)
        Config.set(tm_q, 'burst_read', '24')
        Config.set(tm_q, 'burst_write', '32')
        Config.set(tm_q, 'cfg', '/tmp/full_tm_profile_10G.cfg')

        return Config

    def get_sink_swq(self, parser, pipeline, k, index):
        global sw_q, sink_q
        sink = ""
        pktq = parser.get(pipeline, k)
        if "SINK" in pktq:
            self.sink_q += 1
            sink = " SINK%s" % str(self.sink_q)
        if "TM" in pktq:
            sink = " TM%s" % str(index)
        pktq = "SWQ%s" % str(self.sw_q) + sink
        return pktq

    def vpe_upstream(self, vnf_cfg, index):
        parser = six.moves.configparser.SafeConfigParser()
        parser.read(os.path.join(vnf_cfg, 'vpe_upstream'))
        for pipeline in parser.sections():
            for (k, v) in parser.items(pipeline):
                if k == "pktq_in":
                    if "RXQ" in v:
                        parser.set(pipeline, k,
                                   "RXQ%s.0" % self.priv_ports[index])
                    else:
                        parser.set(pipeline, k,
                                   self.get_sink_swq(parser, pipeline,
                                                     k, index))
                if k == "pktq_out":
                    if "TXQ" in v:
                        parser.set(pipeline, k,
                                   "TXQ%s.0" % self.pub_ports[index])
                    else:
                        self.sw_q += 1
                        parser.set(pipeline, k,
                                   self.get_sink_swq(parser, pipeline,
                                                     k, index))
            new_pipeline = 'PIPELINE%s' % self.n_pipeline
            if new_pipeline != pipeline:
                parser._sections[new_pipeline] = parser._sections[pipeline]
                parser._sections.pop(pipeline)
            self.n_pipeline += 1
        return parser

    def vpe_downstream(self, vnf_cfg, index):
        parser = six.moves.configparser.SafeConfigParser()
        parser.read(os.path.join(vnf_cfg, 'vpe_downstream'))
        for pipeline in parser.sections():
            for (k, v) in parser.items(pipeline):
                if k == "pktq_in":
                    if "RXQ" in v:
                        rxq = "RXQ%s.0" % self.pub_ports[index]
                        if "TM" in v:
                            rxq = rxq + " TM%s" % str(index)
                        parser.set(pipeline, k, rxq)
                    else:
                        parser.set(pipeline, k,
                                   self.get_sink_swq(parser, pipeline,
                                                     k, index))
                if k == "pktq_out":
                    if "TXQ" in v:
                        txq = "TXQ%s.0" % self.priv_ports[index]
                        if "TM" in v:
                            txq = txq + " TM%s" % str(index)
                        parser.set(pipeline, k, txq)
                    else:
                        self.sw_q += 1
                        parser.set(pipeline, k,
                                   self.get_sink_swq(parser, pipeline,
                                                     k, index))
            new_pipeline = 'PIPELINE%s' % self.n_pipeline
            if new_pipeline != pipeline:
                parser._sections[new_pipeline] = parser._sections[pipeline]
                parser._sections.pop(pipeline)
            self.n_pipeline += 1
        return parser

    def create_vpe_config(self, vnf_cfg):
        Config = six.moves.configparser.ConfigParser()
        vpe_cfg = os.path.join(vnf_cfg, "vpe_config")
        cfgfile = open(vpe_cfg, 'w')
        Config = self.vpe_initialize(Config)
        Config = self.vpe_rxq(Config)
        Config.write(cfgfile)
        for index in range(0, len(self.priv_ports)):
            Config = self.vpe_upstream(vnf_cfg, index)
            Config.write(cfgfile)
            Config = self.vpe_downstream(vnf_cfg, index)
            Config = self.vpe_tmq(Config, index)
            Config.write(cfgfile)
        cfgfile.close()

    def get_firewall_script(self, pipeline, ip):
        fwl = ""
        ip_addr = ip.split('.')
        ip_addr[-1] = str(0)
        for i in range(256):
            ip_addr[-2] = str(i)
            ip = '.'.join(ip_addr)
            fwl += 'p {0} firewall add priority 1 ipv4  {1} 24 0.0.0.0 0 0 '\
                   '65535 0 65535 6 0xFF port 0\n'.format(pipeline, ip)
        fwl += 'p {0} firewall add default 1\n\n'.format(pipeline)
        return fwl

    def get_flow_classfication_script(self, pipeline):
        fwl = ""
        fwl += 'p {0} flow add qinq 128 512 port 0 id 1\n'.format(pipeline)
        fwl += 'p {0} flow add default 1\n\n'.format(pipeline)
        return fwl

    def get_flow_action(self, pipeline):
        fwl = ""
        fwl += 'p %s action flow bulk /tmp/action_bulk_512.txt\n\n' % pipeline
        return fwl

    def get_flow_action2(self, pipeline):
        fwl = ""
        fwl += 'p %s action flow bulk /tmp/action_bulk_512.txt\n' % pipeline
        g = itertools.cycle('GYR')
        for i in range(64):
            fwl += 'p {0} action dscp {1} class {2} color {3}\n'.format(
                   pipeline, i, i % 4, next(g))

        return fwl

    def get_route_script(self, pipe_line_id, ip, mac_addr):
        fwl = ''
        ip_addr = ip.split('.')
        ip_addr[-1] = str(0)
        for i in range(0, 256, 8):
            ip_addr[-2] = str(i)
            ip = '.'.join(ip_addr)
            fwl += 'p {0} route add {1} 21 port 0 ether {2} mpls '\
                   '0:{3}\n'.format(pipe_line_id, ip, mac_addr, i)
        fwl += 'p {0} route add default 1\n\n'.format(pipe_line_id)
        return fwl

    def get_route_script2(self, pipe_line_id, ip, mac_addr):
        fwl = ''
        ip_addr = ip.split('.')
        ip_addr[-1] = str(0)
        mask = 24
        for i in range(0, 256):
            ip_addr[-2] = str(i)
            ip = '.'.join(ip_addr)
            fwl += 'p {0} route add {1} {2} port 0 ether {3} qinq '\
                   '0 {4}\n'.format(pipe_line_id, ip, mask, mac_addr, i)
        fwl += 'p {0} route add default 1\n\n'.format(pipe_line_id)
        return fwl

    def generate_vpe_script(self, interfaces):
        num_pipe = 1
        fwl = ""
        for idx in range(0, len(self.priv_ports)):
            priv_port = self.priv_ports[idx]
            pub_port = self.pub_ports[idx]
            dst_port0_ip = \
                interfaces[priv_port]["virtual-interface"]["dst_ip"]
            dst_port1_ip = \
                interfaces[pub_port]["virtual-interface"]["dst_ip"]
            dst_port0_mac = \
                interfaces[priv_port]["virtual-interface"]["dst_mac"]
            dst_port1_mac = \
                interfaces[pub_port]["virtual-interface"]["dst_mac"]

            fwl += self.get_firewall_script(num_pipe, dst_port0_ip)
            num_pipe += 1
            fwl += self.get_flow_classfication_script(num_pipe)
            num_pipe += 1
            fwl += self.get_flow_action(num_pipe)
            num_pipe += 1
            fwl += self.get_flow_action2(num_pipe)
            num_pipe += 1
            fwl += self.get_route_script(num_pipe, dst_port1_ip, dst_port1_mac)
            num_pipe += 1
            fwl += \
                self.get_route_script2(num_pipe, dst_port0_ip, dst_port0_mac)
            num_pipe += 4

        return fwl


class VpeApproxVnf(GenericVNF):
    """ This class handles vPE VNF model-driver definitions """

    def __init__(self, vnfd):
        super(VpeApproxVnf, self).__init__(vnfd)
        self.socket = None
        self.q_in = Queue()
        self.q_out = Queue()
        self.vnf_cfg = None
        self._vnf_process = None
        self.connection = None
        self.resource = None

    def _resource_collect_start(self):
        self.resource.initiate_systemagent(self.bin_path)
        self.resource.start()
        self.resource.amqp_process_for_nfvi_kpi()

    def _resource_collect_stop(self):
        if self.resource:
            self.resource.stop()

    def _collect_resource_kpi(self):
        result = {}

        status = self.resource.check_if_sa_running("collectd")[0]
        if status:
            result = self.resource.amqp_collect_nfvi_kpi()

        result = {"core": result}

        return result

    @classmethod
    def __setup_hugepages(cls, connection):
        hugepages = \
            connection.execute(
                "awk '/Hugepagesize/ { print $2$3 }' < /proc/meminfo")[1]
        hugepages = hugepages.rstrip()

        memory_path = \
            '/sys/kernel/mm/hugepages/hugepages-%s/nr_hugepages' % hugepages
        connection.execute("awk -F: '{ print $1 }' < %s" % memory_path)

        pages = 4096 if hugepages.rstrip() == "2048kB" else 4
        connection.execute("sudo echo %s > %s" % (pages, memory_path))

    def setup_vnf_environment(self, connection):
        ''' setup dpdk environment needed for vnf to run '''

        self.__setup_hugepages(connection)
        connection.execute("sudo modprobe uio && sudo modprobe igb_uio")

        exit_status = connection.execute("lsmod | grep -i igb_uio")[0]
        if exit_status == 0:
            return

        dpdk = os.path.join(self.bin_path, "dpdk-16.07")
        dpdk_setup = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "nsb_setup.sh"))
        status = connection.execute("ls {} >/dev/null 2>&1".format(dpdk))[0]
        if status:
            connection.execute("sudo bash %s dpdk >/dev/null 2>&1" %
                               dpdk_setup)

    def _get_cpu_sibling_list(self):
        cpu_topo = []
        for core in CORES:
            sys_cmd = \
                "/sys/devices/system/cpu/cpu%s/topology/thread_siblings_list" \
                % core
            cpuid = \
                self.connection.execute("awk -F: '{ print $1 }' < %s" %
                                        sys_cmd)[1]
            cpu_topo += \
                [(idx) if idx.isdigit() else idx for idx in cpuid.split(',')]

        return [cpu.strip() for cpu in cpu_topo]

    def scale(self, flavor=""):
        ''' scale vnfbased on flavor input '''
        super(VpeApproxVnf, self).scale(flavor)

    def get_nfvi_type(self, scenario_cfg):
        tc_data = None
        tc_file = '%s.yaml' % scenario_cfg['tc']

        with open(tc_file) as tfh:
            tc_data = yaml.safe_load(tfh)

        nfvi_type = tc_data['context'].get('nfvi_type', 'baremetal')
        return nfvi_type

    def instantiate(self, scenario_cfg, context_cfg):
        vnf_cfg = scenario_cfg['vnf_options']['vpe']['cfg']

        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)

        self.tc_file_name = '{0}.yaml'.format(scenario_cfg['tc'])

        self.setup_vnf_environment(self.connection)

        self.nfvi_type = self.get_nfvi_type(scenario_cfg)
        self.topology = os.path.abspath(scenario_cfg['topology'])

        cores = self._get_cpu_sibling_list()
        self.resource = ResourceProfile(self.vnfd, cores)

        self.connection.execute("sudo pkill vPE_vnf")
        dpdk_nic_bind = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "dpdk_nic_bind.py"))

        interfaces = self.vnfd["vdu"][0]['external-interface']
        self.socket = \
            next((0 for v in interfaces
                  if v['virtual-interface']["vpci"][5] == "0"), 1)

        bound_pci = [v['virtual-interface']["vpci"] for v in interfaces]
        for vpci in bound_pci:
            self.connection.execute(
                "sudo %s --force -b igb_uio %s" % (dpdk_nic_bind, vpci))
        queue_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, "pipeline>")
        self._vnf_process = multiprocessing.Process(target=self._run_vpe,
                                                    args=(queue_wrapper,
                                                          vnf_cfg,))
        self._vnf_process.start()
        buf = []
        time.sleep(WAIT_TIME)  # Give some time for config to load
        while True:
            message = ''
            while self.q_out.qsize() > 0:
                buf.append(self.q_out.get())
                message = ''.join(buf)
                if "pipeline>" in message:
                    LOG.info("VPE VNF is up and running.")
                    queue_wrapper.clear()
                    self._resource_collect_start()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting vPE VNF.")

            LOG.info("Waiting for VNF to start.. ")
            time.sleep(3)
            if not self._vnf_process.is_alive():
                raise RuntimeError("vPE VNF process died.")

    def _get_ports_gateway(self, name):
        if 'routing_table' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['routing_table']

            for route in routing_table:
                if name == route['if']:
                    return route['gateway']

    def terminate(self):
        self.execute_command("quit")
        if self._vnf_process:
            self._vnf_process.terminate()
        self._resource_collect_stop()

    def _run_vpe(self, filewrapper, vnf_cfg):
        mgmt_interface = self.vnfd["mgmt-interface"]

        self.connection = ssh.SSH.from_node(mgmt_interface)
        self.connection.wait()

        interfaces = self.vnfd["vdu"][0]['external-interface']
        port0_ip = ipaddress.ip_interface(six.text_type(
            "%s/%s" % (interfaces[0]["virtual-interface"]["local_ip"],
                       interfaces[0]["virtual-interface"]["netmask"])))
        port1_ip = ipaddress.ip_interface(six.text_type(
            "%s/%s" % (interfaces[1]["virtual-interface"]["local_ip"],
                       interfaces[1]["virtual-interface"]["netmask"])))
        dst_port0_ip = ipaddress.ip_interface(
            u"%s/%s" % (interfaces[0]["virtual-interface"]["dst_ip"],
                        interfaces[0]["virtual-interface"]["netmask"]))
        dst_port1_ip = ipaddress.ip_interface(
            u"%s/%s" % (interfaces[1]["virtual-interface"]["dst_ip"],
                        interfaces[1]["virtual-interface"]["netmask"]))

        vpe_vars = {"port0_local_ip": port0_ip.ip.exploded,
                    "port0_dst_ip": dst_port0_ip.ip.exploded,
                    "port0_local_ip_hex":
                    self._ip_to_hex(port0_ip.ip.exploded),
                    "port0_prefixlen": port0_ip.network.prefixlen,
                    "port0_netmask": port0_ip.network.netmask.exploded,
                    "port0_netmask_hex":
                    self._ip_to_hex(port0_ip.network.netmask.exploded),
                    "port0_local_mac":
                    interfaces[0]["virtual-interface"]["local_mac"],
                    "port0_dst_mac":
                    interfaces[0]["virtual-interface"]["dst_mac"],
                    "port0_gateway":
                    self._get_ports_gateway(interfaces[0]["name"]),
                    "port0_local_network":
                    port0_ip.network.network_address.exploded,
                    "port0_prefix": port0_ip.network.prefixlen,
                    "port1_local_ip": port1_ip.ip.exploded,
                    "port1_dst_ip": dst_port1_ip.ip.exploded,
                    "port1_local_ip_hex":
                    self._ip_to_hex(port1_ip.ip.exploded),
                    "port1_prefixlen": port1_ip.network.prefixlen,
                    "port1_netmask": port1_ip.network.netmask.exploded,
                    "port1_netmask_hex":
                    self._ip_to_hex(port1_ip.network.netmask.exploded),
                    "port1_local_mac":
                    interfaces[1]["virtual-interface"]["local_mac"],
                    "port1_dst_mac":
                    interfaces[1]["virtual-interface"]["dst_mac"],
                    "port1_gateway":
                    self._get_ports_gateway(interfaces[1]["name"]),
                    "port1_local_network":
                    port1_ip.network.network_address.exploded,
                    "port1_prefix": port1_ip.network.prefixlen,
                    "port0_local_ip6": self._get_port0localip6(),
                    "port1_local_ip6": self._get_port1localip6(),
                    "port0_prefixlen6": self._get_port0prefixlen6(),
                    "port1_prefixlen6": self._get_port1prefixlen6(),
                    "port0_gateway6": self._get_port0gateway6(),
                    "port1_gateway6": self._get_port1gateway6(),
                    "port0_dst_ip_hex6": self._get_port0localip6(),
                    "port1_dst_ip_hex6": self._get_port1localip6(),
                    "port0_dst_netmask_hex6": self._get_port0prefixlen6(),
                    "port1_dst_netmask_hex6": self._get_port1prefixlen6(),
                    "bin_path": self.bin_path,
                    "socket": self.socket}

        with open(self.tc_file_name) as tc_file:
            tc_yaml = yaml.load(tc_file.read())

        topology = tc_yaml['scenarios'][0]['topology']
        self.generate_port_pairs(topology)
        self.priv_ports = [int(x[0][-1]) for x in self.tg_port_pairs]
        self.pub_ports = [int(x[1][-1]) for x in self.tg_port_pairs]
        self.my_ports = list(set(self.priv_ports).union(set(self.pub_ports)))

        vpe_conf = ConfigCreate(self.priv_ports, self.pub_ports, self.socket)
        vpe_conf.create_vpe_config(vnf_cfg)
        for cfg in os.listdir(vnf_cfg):
            vpe_config = ""
            with open(os.path.join(vnf_cfg, cfg), 'r') as vpe_cfg:
                vpe_config = vpe_cfg.read()

            self._provide_config_file(cfg, vpe_config, vpe_vars)
        vpe_script = vpe_conf.generate_vpe_script(interfaces)
        self._provide_config_file("vpe_script", vpe_script, vpe_vars)

        LOG.info("Provision and start the vPE")
        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path, "vPE_vnf"))
        ports_len_hex = \
            hex(eval(
                '0b' + "".join([str(1) for x in range(len(self.my_ports))])))
        cmd = VPE_PIPELINE_COMMAND.format(ports_len_hex=ports_len_hex,
                                          cfg_file="/tmp/vpe_config",
                                          script="/tmp/vpe_script",
                                          tool_path=tool_path)
        self.connection.run(cmd, stdin=filewrapper, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    def _provide_config_file(self, prefix, template, args):
        cfg, cfg_content = tempfile.mkstemp()
        cfg = os.fdopen(cfg, "w+")
        cfg.write(template.format(**args))
        cfg.close()
        cfg_file = "/tmp/%s" % prefix
        self.connection.put(cfg_content, cfg_file)
        return cfg_file

    def execute_command(self, cmd):
        ''' send cmd to vnf process '''
        LOG.info("VPE command: %s", cmd)
        output = []
        if self.q_in:
            self.q_in.put(cmd + "\r\n")
            time.sleep(3)
            while self.q_out.qsize() > 0:
                output.append(self.q_out.get())
        return "".join(output)

    def collect_kpi(self):
        result = self.get_stats_vpe()
        collect_stats = self._collect_resource_kpi()
        result["collect_stats"] = collect_stats
        LOG.debug("vPE KPIs: %s", result)
        return result

    def get_stats_vpe(self):
        ''' get vpe statistics '''
        result = {'pkt_in_up_stream': 0, 'pkt_drop_up_stream': 0,
                  'pkt_in_down_stream': 0, 'pkt_drop_down_stream': 0}
        up_stat_commands = ['p 5 stats port in 0', 'p 5 stats port out 0']
        down_stat_commands = ['p 9 stats port in 0', 'p 9 stats port out 0']
        pattern = \
            "Pkts in:\\s(\\d+)\\r\\n\\tPkts dropped by " \
            "AH:\\s(\\d+)\\r\\n\\tPkts dropped by other:\\s(\\d+)"

        for cmd in up_stat_commands:
            stats = self.execute_command(cmd)
            match = re.search(pattern, stats, re.MULTILINE)
            if match:
                result["pkt_in_up_stream"] = \
                    result.get("pkt_in_up_stream", 0) + int(match.group(1))
                result["pkt_drop_up_stream"] = \
                    result.get("pkt_drop_up_stream", 0) + \
                    int(match.group(2)) + int(match.group(3))

        for cmd in down_stat_commands:
            stats = self.execute_command(cmd)
            match = re.search(pattern, stats, re.MULTILINE)
            if match:
                result["pkt_in_down_stream"] = \
                    result.get("pkt_in_down_stream", 0) + int(match.group(1))
                result["pkt_drop_down_stream"] = \
                    result.get("pkt_drop_down_stream", 0) + \
                    int(match.group(2)) + int(match.group(3))
        return result
