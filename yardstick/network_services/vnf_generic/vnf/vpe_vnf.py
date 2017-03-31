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
import six

from yardstick import ssh
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.utils import provision_tool
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.nfvi.resource import ResourceProfile

LOG = logging.getLogger(__name__)
VPE_PIPELINE_COMMAND = \
    'sudo {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'
CORES = ['0', '1', '2', '3', '4', '5']
WAIT_TIME = 20


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

    def _resource_collect_stop(self):
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

    def instantiate(self, scenario_cfg, context_cfg):
        vnf_cfg = scenario_cfg['vnf_options']['vpe']['cfg']

        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)

        self.tc_file_name = '{0}.yaml'.format(scenario_cfg['tc'])

        self.setup_vnf_environment(self.connection)

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

        for cfg in os.listdir(vnf_cfg):
            vpe_config = ""
            with open(os.path.join(vnf_cfg, cfg), 'r') as vpe_cfg:
                vpe_config = vpe_cfg.read()

            self._provide_config_file(cfg, vpe_config, vpe_vars)

        LOG.info("Provision and start the vPE")
        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path, "vPE_vnf"))
        cmd = VPE_PIPELINE_COMMAND.format(cfg_file="/tmp/vpe_config",
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
        LOG.debug("vPE collet Kpis: %s", result)
        return result

    def get_stats_vpe(self):
        ''' get vpe statistics '''
        result = {'pkt_in_up_stream': 0, 'pkt_drop_up_stream': 0,
                  'pkt_in_down_stream': 0, 'pkt_drop_down_stream': 0}
        up_stat_commands = ['p 5 stats port in 0', 'p 5 stats port out 0',
                            'p 5 stats port out 1']
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
