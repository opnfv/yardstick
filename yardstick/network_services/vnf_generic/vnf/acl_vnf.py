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
from __future__ import print_function
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
from yardstick.benchmark.scenarios.networking.vnf_generic import find_relative_file
from yardstick.common.utils import parse_cpuinfo
from yardstick.network_services.utils import provision_tool
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.nfvi.resource import ResourceProfile

LOG = logging.getLogger(__name__)

# ACL should work the same on all systems, we can provide the binary
ACL_PIPELINE_COMMAND = 'sudo {tool_path} -p 0x3 -f {cfg_file} -s {script}'


class AclApproxVnf(GenericVNF):

    def __init__(self, vnfd):
        super(AclApproxVnf, self).__init__(vnfd)
        self.socket = None
        self.mgmt_interface = self.vnfd["mgmt-interface"]
        self.q_in = Queue()
        self.q_out = Queue()
        self.vnf_cfg = None
        self._vnf_process = None
        self.connection = None
        self.resource = None
        self.deploy = None

    def _resource_collect_start(self):
        self.resource.enable = False
        self.resource.initiate_systemagent(self.bin_path)
        self.resource.start()
        # self.resource.amqp_process_for_nfvi_kpi()

    def _resource_collect_stop(self):
        self.resource.stop()

    def _collect_resource_kpi(self):
        result = {}

        status = self.resource.check_if_sa_running("collectd")[0]
        if status:
            result = self.resource.amqp_collect_nfvi_kpi()

        result = {"core": result}

        return result

    def setup_vnf_environment(self, connection):
        ''' setup dpdk environment needed for vnf to run '''

        self.setup_hugepages(connection)
        connection.execute("sudo modprobe uio && sudo modprobe igb_uio")

        exit_status = connection.execute("lsmod | grep -i igb_uio")[0]
        if exit_status == 0:
            return

        dpdk = os.path.join(self.bin_path, "dpdk-16.07")
        # dpdk_setup = \
        #     provision_tool(self.connection,
        #                    os.path.join(self.bin_path, "nsb_setup.sh"))
        status = connection.execute("which {}".format(dpdk))[0]
        # if status:
        #     connection.execute("bash %s dpdk >/dev/null 2>&1" % dpdk_setup)

    def scale(self, flavor=""):
        ''' scale vnfbased on flavor input '''
        super(AclApproxVnf, self).scale(flavor)

    def deploy_acl_vnf(self):
        self.deploy.deploy_vnfs("vACL")

    def get_nfvi_type(self, scenario_cfg):
        tc_data = {}
        # tc_file = '%s.yaml' % scenario_cfg['tc']
        #
        # with open(tc_file) as tfh:
        #     tc_data = yaml.safe_load(tfh)

        nfvi_type = tc_data['context'].get('nfvi_type', 'baremetal')
        return nfvi_type

    DPDK_STATUS_DRIVER_RE = re.compile(r"(\d{2}:\d{2}\.\d).*drv=([-\w]+)")

    @staticmethod
    def find_pci(pci, bound_pci):
        # we have to substring match PCI bus address from the end
        return any(b.endswith(pci) for b in bound_pci)

    def find_used_drivers(self, bound_pci, dpdk_status):
        used_drivers = {m[0]: m[1] for m in
                        self.DPDK_STATUS_DRIVER_RE.findall(dpdk_status) if
                        self.find_pci(m[0], bound_pci)}
        return used_drivers

    def instantiate(self, scenario_cfg, context_cfg):
        cores = ["0", "1", "2", "3", "4"]
        # vnf_cfg is a dir
        self.vnf_cfg = os.path.join(scenario_cfg['task_path'],
                                    scenario_cfg['vnf_options']['acl']['cfg'])

        rule_file = find_relative_file(scenario_cfg['vnf_options']['acl']['rules'],
                                       scenario_cfg['task_path'])
        if not self.connection:
            self.connection = ssh.SSH.from_node(self.mgmt_interface)

        rc, stdout, stderr = self.connection.execute("cat /proc/cpuinfo")
        # { socket: { core: {proc: (socket, core, proc), proc: (socket, core, proc}}
        self.cpu_topology = parse_cpuinfo(stdout)
        LOG.debug(self.cpu_topology)
        rc, stdout, stderr = self.connection.execute("cat /proc/meminfo")

        # self.deploy = OPNFVSampleVNF(self.connection, self.bin_path)
        # self.deploy_acl_vnf()

        self.setup_vnf_environment(self.connection)

        self.resource = ResourceProfile(self.vnfd, cores)

        self.connection.execute("sudo pkill vACL")
        self.dpdk_nic_bind = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "dpdk-devbind.py"))
        interfaces = self.vnfd["vdu"][0]['external-interface']
        # socket is based on PCI?  really
        self.socket = \
            next((0 for v in interfaces
                  if v['virtual-interface']["vpci"][5] == "0"), 1)

        bound_pci = [v['virtual-interface']["vpci"] for v in interfaces]
        rc, dpdk_status, _ = self.connection.execute(
            "sudo {dpdk_nic_bind} -s".format(dpdk_nic_bind=self.dpdk_nic_bind))
        self.used_drivers = self.find_used_drivers(bound_pci, dpdk_status)
        for vpci in bound_pci:
            cmd = "sudo {dpdk_nic_bind} --force -b igb_uio {vpci}".format(
                vpci=vpci, dpdk_nic_bind=self.dpdk_nic_bind)
            self.connection.execute(cmd)
            time.sleep(2)
        self.connection.execute("sudo {dpdk_nic_bind} -s".format(dpdk_nic_bind=self.dpdk_nic_bind))
        acl_rules = self._parse_rule_file(rule_file)
        queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, "pipeline>")
        self._vnf_process = \
            multiprocessing.Process(target=self._run_acl,
                                    args=(queue_wrapper, acl_rules))
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
                    LOG.info("ACL VNF is up and running.")
                    queue_wrapper.clear()
                    # temp disable collected
                    # self._resource_collect_start()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting VNF.")
            LOG.info("Waiting for ACL VNF to start.. ")
            time.sleep(1)
        return self._vnf_process.is_alive()

    def terminate(self):
        self.execute_command("quit")
        if self._vnf_process:
            self._vnf_process.terminate()
        # we may not have ssh connection still at this point, so reconnect
        # not sure why
        if not self.connection:
            self.connection = ssh.SSH.from_node(self.mgmt_interface)
        self.connection.wait()
        self.connection.execute("sudo pkill vACL")
        for vpci, driver in getattr(self, "used_drivers", {}).items():
            self.connection.execute(
                "sudo {dpdk_nic_bind} --force  -b {driver}"
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
        except Exception:
            LOG.debug("Failed to read the yaml %s", exc_info=True)

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
            # Now all rules in sample ACL file are TCP.
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

    def _run_acl(self, filewrapper, rules=""):
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
        dst_port0_ip = \
            ipaddress.ip_interface(six.text_type(
                "%s/%s" % (interfaces[0]["virtual-interface"]["dst_ip"],
                           interfaces[0]["virtual-interface"]["netmask"])))
        dst_port1_ip = \
            ipaddress.ip_interface(six.text_type(
                "%s/%s" % (interfaces[1]["virtual-interface"]["dst_ip"],
                           interfaces[1]["virtual-interface"]["netmask"])))

        acl_vars = {"port0_local_ip": port0_ip.ip.exploded,
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
            acl_config = ""
            with open(os.path.join(self.vnf_cfg, cfg), 'r') as acl_cfg:
                acl_config = acl_cfg.read()

            content = self.render_template_config(acl_config, acl_vars)
            LOG.debug(content)
            self.upload_config_file(cfg, content)

        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path,
                                                "vACL"))
        time.sleep(1)
        cmd = ACL_PIPELINE_COMMAND.format(cfg_file="/tmp/acl_config",
                                          script="/tmp/acl_script",
                                          tool_path=tool_path)
        LOG.debug(cmd)
        self.connection.run(cmd, stdin=filewrapper, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    @staticmethod
    def render_template_config(template, args):
        return template.format(**args)

    def upload_config_file(self, prefix, content):
        with tempfile.NamedTemporaryFile(mode="w", delete=True) as cfg:
            cfg.write(content)
            cfg.flush()
            cfg_file = "/tmp/%s" % prefix
            self.connection.put(cfg.name, cfg_file)
            return cfg_file

    def execute_command(self, cmd):
        LOG.info("ACL command: %s", cmd)
        self.q_in.put(cmd + "\r\n")
        time.sleep(2)
        output = []
        while self.q_out.qsize() > 0:
            output.append(self.q_out.get())
        return "".join(output)

    def collect_kpi(self):
        stats = self.get_stats_acl()
        collect_stats = self._collect_resource_kpi()
        pattern = r"ACL TOTAL:\stpkts_processed:\s(\d+),\spkts_drop:\s(\d+)," \
            r"\spkts_received:\s(\d+),"
        m = re.search(pattern, stats, re.MULTILINE)
        result = {"packets_in": 0, "packets_fwd": 0, "packets_dropped": 0}
        if m:
            result.update({"packets_in": int(m.group(3)),
                           "packets_fwd": int(m.group(1)),
                           "packets_dropped": int(m.group(2)),
                           "collect_stats": collect_stats})
        LOG.debug("ACL collect KPIs %s", result)
        return result

    def get_stats_acl(self):
        """
        Method for checking the ACL statistics

        :return:
           ACL statistics
        """
        cmd = 'p acl stats'
        out = self.execute_command(cmd)
        return out
