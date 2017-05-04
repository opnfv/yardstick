# Copyright (c) 2016 Intel Corporation
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
import tempfile
from multiprocessing import Queue
import multiprocessing
import time
import os
import logging
import re
import ipaddress
import six

from yardstick import ssh
from yardstick.network_services.utils import provision_tool
from yardstick.network_services.helpers.samplevnf_helper import OPNFVSampleVNF
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.nfvi.resource import ResourceProfile

log = logging.getLogger(__name__)

# CGNAPT should work the same on all systems, we can provide the binary
CGNAPT_PIPELINE_COMMAND = '{tool_path} -p 0x3 -f {cfg_file} -s {script}'


class CgnaptApproxVnf(GenericVNF):

    def __init__(self, vnfd):
        super(CgnaptApproxVnf, self).__init__(vnfd)
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

        pages = 16384 if hugepages.rstrip() == "2048kB" else 16
        connection.execute("echo %s > %s" % (pages, memory_path))

    def setup_vnf_environment(self, connection):
        ''' setup dpdk environment needed for vnf to run '''

        self.__setup_hugepages(connection)
        connection.execute("modprobe uio && modprobe igb_uio")

        exit_status = connection.execute("lsmod | grep -i igb_uio")[0]
        if exit_status == 0:
            return

        dpdk = os.path.join(self.bin_path, "dpdk-16.07")
        dpdk_setup = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "nsb_setup.sh"))
        status = connection.execute("ls {} >/dev/null 2>&1".format(dpdk))[0]
        if status:
            connection.execute("bash %s dpdk >/dev/null 2>&1" % dpdk_setup)

    def scale(self, flavor=""):
        ''' scale vnfbased on flavor input '''
        super(CgnaptApproxVnf, self).scale(flavor)

    def deploy_cgnapt_vnf(self):
        self.deploy.deploy_vnfs("vACL")

    def instantiate(self, scenario_cfg, context_cfg):
        cores = ["0", "1", "2", "3", "4"]
        self.vnf_cfg = scenario_cfg['vnf_options']['cgnapt']['cfg']
        self.nodes = scenario_cfg['nodes']

        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)

        self.deploy = OPNFVSampleVNF(self.connection, self.bin_path)
        self.deploy_cgnapt_vnf()

        self.setup_vnf_environment(self.connection)
        self.resource = ResourceProfile(self.vnfd, cores)

        self.connection.execute("pkill vCGNAPT")
        self.dpdk_nic_bind = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "dpdk_nic_bind.py"))
        interfaces = self.vnfd["vdu"][0]['external-interface']
        self.socket = \
            next((0 for v in interfaces
                  if v['virtual-interface']["vpci"][5] == "0"), 1)

        bound_pci = [v['virtual-interface']["vpci"] for v in interfaces]
        rc, dpdk_status, _ = self.connection.execute(
            "{dpdk_nic_bind} -s".format(dpdk_nic_bind=self.dpdk_nic_bind))
        pattern = "(\d{2}:\d{2}\.\d).*drv=(\w+)"
        self.used_drivers = \
            {m[0]: m[1] for m in re.findall(pattern, dpdk_status) if
             m[0] in bound_pci}
        for vpci in bound_pci:
            self.connection.execute(
                "{dpdk_nic_bind} --force -b igb_uio"
                " {vpci}".format(vpci=vpci, dpdk_nic_bind=self.dpdk_nic_bind))
            time.sleep(2)
        queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, "pipeline>")
        self._vnf_process = \
            multiprocessing.Process(target=self._run_vcgnapt,
                                    args=(queue_wrapper,))
        self._vnf_process.start()
        buf = []
        while True:
            if not self._vnf_process.is_alive():
                raise RuntimeError("VNF process died.")
            message = ""
            while self.q_out.qsize() > 0:
                buf.append(self.q_out.get())
                message = ''.join(buf)
                if "pipeline>" in message:
                    log.info("CGNAPT VNF is up and running.")
                    self._add_static_cgnat(self.nodes, interfaces)
                    queue_wrapper.clear()
                    self._resource_collect_start()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting VNF.")
            log.info("Waiting for CGNAPT VNF to start.. ")
            time.sleep(1)
        return self._vnf_process.is_alive()

    def terminate(self):
        self.execute_command("quit")
        self._vnf_process.terminate()
        self.connection.execute("pkill vCGNAPT")
        for vpci, driver in self.used_drivers.items():
            self.connection.execute(
                "{dpdk_nic_bind} --force  -b {driver}"
                " {vpci}".format(vpci=vpci, driver=driver,
                                 dpdk_nic_bind=self.dpdk_nic_bind))
        self._resource_collect_stop()

    def _get_ports_gateway(self, name):
        if 'routing_table' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['routing_table']

            for route in routing_table:
                if name == route['if']:
                    return route['gateway']

    def _add_static_cgnat(self, nodes, interfaces):
        if len(nodes) == 2:
            cgnapt_config = self._get_cgnapt_config(interfaces)
            cmd = "p 5 entry addm {port0_gateway} 1 152.16.40.10 1 0 32 " \
                  "65535 65535 65535".format(**cgnapt_config)
            self.execute_command(cmd)
            time.sleep(2)

    def _get_cgnapt_config(self, interfaces):
        port0_ip = ipaddress.ip_interface(six.text_type(
            "%s/%s" % (interfaces[0]["virtual-interface"]["local_ip"],
                       interfaces[0]["virtual-interface"]["netmask"])))
        port1_ip = ipaddress.ip_interface(six.text_type(
            "%s/%s" % (interfaces[1]["virtual-interface"]["local_ip"],
                       interfaces[1]["virtual-interface"]["netmask"])))
        dst_port0_ip = \
            ipaddress.ip_interface(six.text_type(
                "%s/%s" % (interfaces[0]["virtual-interface"]["dst_ip"],
                           interfaces[0]["virtual-interface"]["netmask"])))
        dst_port1_ip = \
            ipaddress.ip_interface(six.text_type(
                "%s/%s" % (interfaces[1]["virtual-interface"]["dst_ip"],
                           interfaces[1]["virtual-interface"]["netmask"])))

        cgnapt_vars = {"port0_local_ip": port0_ip.ip.exploded,
                       "port0_dst_ip": dst_port0_ip.ip.exploded,
                       "port0_dst_ip_hex":
                       self._ip_to_hex(dst_port0_ip.ip.exploded),
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
                       "port1_dst_ip_hex":
                       self._ip_to_hex(dst_port1_ip.ip.exploded),
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
        return cgnapt_vars

    def _run_vcgnapt(self, filewrapper):
        vcgnapt_config = ""
        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)
        interfaces = self.vnfd["vdu"][0]['external-interface']

        vcgnapt_vars = self._get_cgnapt_config(interfaces)
        log.debug(vcgnapt_vars)
        # Read the pipeline config and populate the data
        for cfg in os.listdir(self.vnf_cfg):
            vcgnapt_config = ""
            with open(os.path.join(self.vnf_cfg, cfg), 'r') as vcgnapt_cfg:
                vcgnapt_config = vcgnapt_cfg.read()

            self._provide_config_file(cfg, vcgnapt_config, vcgnapt_vars)

        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path,
                                                "vCGNAPT"))
        time.sleep(1)
        cmd = CGNAPT_PIPELINE_COMMAND.format(cfg_file="/tmp/cgnapt_config",
                                             script="/tmp/cgnapt_script",
                                             tool_path=tool_path)
        self.connection.run(cmd, stdin=filewrapper, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    def _provide_config_file(self, prefix, template, vars):
        cfg, cfg_content = tempfile.mkstemp()
        cfg = os.fdopen(cfg, "w+")
        cfg.write(template.format(**vars))
        cfg.close()
        cfg_file = os.path.join("/tmp", prefix)
        self.connection.put(cfg_content, cfg_file)
        return cfg_file

    def execute_command(self, cmd):
        log.info("CGNAPT command: %s", cmd)
        self.q_in.put(cmd + "\r\n")
        time.sleep(2)
        output = []
        while self.q_out.qsize() > 0:
            output.append(self.q_out.get())
        return "".join(output)

    def collect_kpi(self):
        result = {"packets_in": 0,
                  "packets_fwd": 0,
                  "packets_dropped": 0,
                  "collect_stats": {}}
        stats = self.get_stats_vcgnapt()
        collect_stats = self._collect_resource_kpi()
        pattern = ("CG-NAPT(.*\n)*Received\s(\d+),Missed\s(\d+),"
                   "Dropped\s(\d+),Translated\s(\d+),ingress")
        m = re.search(pattern, stats, re.MULTILINE)
        if m:
            result["packets_in"] = result.get(
                "packets_in", 0) + int(m.group(2))
            result["packets_fwd"] = result.get(
                "packets_fwd", 0) + int(m.group(5))
            result["packets_dropped"] = result.get(
                "packets_dropped", 0) + int(m.group(4))
        result["collect_stats"] = collect_stats

        log.debug("CGNAPT collect KPIs {0}".format(result))
        return result

    def get_stats_vcgnapt(self):
        """
        Method for checking the CGNAPT statistics

        :return:
           CGNAPT statistics
        """
        cmd = 'p cgnapt stats'
        out = self.execute_command(cmd)
        return out
