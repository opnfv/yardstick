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
import yaml
import six

from yardstick import ssh
from yardstick.network_services.utils import provision_tool
from yardstick.network_services.helpers.samplevnf_helper import OPNFVSampleVNF
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.nfvi.resource import ResourceProfile

log = logging.getLogger(__name__)

# vFW should work the same on all systems, we can provide the binary
FW_PIPELINE_COMMAND = '{tool_path} -p 0x3 -f {cfg_file} -s {script}'


class FWApproxVnf(GenericVNF):

    def __init__(self, vnfd):
        super(FWApproxVnf, self).__init__(vnfd)
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
        super(FWApproxVnf, self).scale(flavor)

    def instantiate(self, scenario_cfg, context_cfg):
        cores = ["0", "1", "2", "3", "4"]
        self.vnf_cfg = scenario_cfg['vnf_options']['vfw']['cfg']

        rule_file = scenario_cfg['vnf_options']['vfw']['rules']
        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                                  password=mgmt_interface["password"])

        self.connection.wait()
        deploy = OPNFVSampleVNF(self.connection, self.bin_path)
        deploy.deploy_vnfs("vFW")
        self.setup_vnf_environment(self.connection)
        self.resource = ResourceProfile(self.vnfd, cores)

        self.connection.execute("pkill vFW")
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
        vfw_rules = self._parse_rule_file(rule_file)
        queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, "pipeline>")
        self._vnf_process = \
            multiprocessing.Process(target=self._run_vfw,
                                    args=(queue_wrapper, vfw_rules))
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
                    log.info("vFW VNF is up and running.")
                    queue_wrapper.clear()
                    self._resource_collect_start()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting VNF.")
            log.info("Waiting for vFW VNF to start.. ")
            time.sleep(1)
        return self._vnf_process.is_alive()

    def terminate(self):
        self.execute_command("quit")
        self._vnf_process.terminate()
        self.connection.execute("pkill vFW")
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

    def _read_yang_model_config(self, yaml_path):
        # TODO: add some error handling in case of empty or non-existing file
        options = {}
        try:
            with open(yaml_path) as f:
                options = yaml.load(f)
        except OSError as e:
            log.debug("Failed to read the yaml {}".format(e))

        return options

    def _parse_rule_file(self, rule_file):
        """
        :param rule_file:
        :return: list of rules
        """
        yang_model = self._read_yang_model_config(rule_file)
        if yang_model:
            return self._get_converted_yang_entries(yang_model)
        else:
            return ""

    def _get_converted_yang_entries(self, yang_model):
        rule = ""
        for ace in yang_model['access-list1']['acl']['access-list-entries']:
            # TODO: resolve ports using topology file and nodes'
            # ids: public or private.
            matches = ace['ace']['matches']
            port0_local_network = \
                ipaddress.ip_interface(six.text_type(
                    matches['destination-ipv4-network'])
                    ).network.network_address.exploded
            port0_prefix = \
                ipaddress.ip_interface(six.text_type(
                    matches['destination-ipv4-network'])).network.prefixlen
            port1_local_network = \
                ipaddress.ip_interface(six.text_type(
                    matches['source-ipv4-network'])
                    ).network.network_address.exploded
            port1_prefix = ipaddress.ip_interface(six.text_type(
                matches['source-ipv4-network'])).network.prefixlen

            lower_dport = matches['destination-port-range']['lower-port']
            upper_dport = matches['destination-port-range']['upper-port']

            lower_sport = matches['source-port-range']['lower-port']
            upper_sport = matches['source-port-range']['upper-port']

            # TODO: proto should be read from file also.
            # Now all rules in sample acl file are TCP.
            rule += "\n\np acl add 1 {0} {1} {2} {3} {4} {5}" \
                    " {6} {7} 0 0 0\n".format(port0_local_network,
                                              port0_prefix,
                                              port1_local_network,
                                              port1_prefix,
                                              lower_dport, upper_dport,
                                              lower_sport, upper_sport)
            rule += "p acl add 1 {0} {1} {2} {3} {4} {5}" \
                    " {6} {7} 0 0 1".format(port1_local_network,
                                            port1_prefix,
                                            port0_local_network,
                                            port0_prefix,
                                            lower_sport, upper_sport,
                                            lower_dport, upper_dport)

        return rule

    def _run_vfw(self, filewrapper, rules=""):
        vfw_config = ""
        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                                  password=mgmt_interface["password"])
        self.connection.wait()
        interfaces = self.vnfd["vdu"][0]['external-interface']
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

        vfw_vars = {"port0_local_ip": port0_ip.ip.exploded,
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
                    "socket": self.socket
                    }

        # Read the pipeline config and populate the data
        for cfg in os.listdir(self.vnf_cfg):
            vfw_config = ""
            with open(os.path.join(self.vnf_cfg, cfg), 'r') as vfw_cfg:
                vfw_config = vfw_cfg.read()

            self._provide_config_file(cfg, vfw_config, vfw_vars)

        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path,
                                                "vFW"))
        time.sleep(1)
        cmd = FW_PIPELINE_COMMAND.format(cfg_file="/tmp/vfw_config",
                                          script="/tmp/vfw_script",
                                          tool_path=tool_path)
        log.debug(cmd)
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
        log.info("vFW command: %s", cmd)
        self.q_in.put(cmd + "\r\n")
        time.sleep(2)
        output = []
        while self.q_out.qsize() > 0:
            output.append(self.q_out.get())
        return "".join(output)

    def collect_kpi(self):
        stats = self.get_stats_vfw()
        collect_stats = self._collect_resource_kpi()
        pattern = ("VFW TOTAL:\spkts_received:\s(\d+),"
                   "\s\"pkts_fw_forwarded\":""\s(\d+),"
                   "\s\"pkts_drop_fw\":\s(\d+),\s")
        m = re.search(pattern, stats, re.MULTILINE)
        result = {"packets_in": 0, "packets_fwd": 0, "packets_dropped": 0}
        if m:
            result.update({"packets_in": int(m.group(1)),
                           "packets_fwd": int(m.group(2)),
                           "packets_dropped": int(m.group(3)),
                           "collect_stats": collect_stats})
        log.debug("vFW collect KPIs {0}".format(result))
        return result

    def get_stats_vfw(self):
        """
        Method for checking the vFW statistics

        :return:
           vFW statistics
        """
        cmd = 'p vfw stats'
        out = self.execute_command(cmd)
        return out
