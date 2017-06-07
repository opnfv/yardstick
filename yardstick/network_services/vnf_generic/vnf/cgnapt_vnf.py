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
import tempfile
from multiprocessing import Queue
import multiprocessing
import time
import os
import logging
import re
import posixpath

from yardstick import ssh
from yardstick.network_services.utils import provision_tool
from yardstick.benchmark.contexts.base import Context
from yardstick.network_services.helpers.samplevnf_helper import \
    MultiPortConfig
from yardstick.network_services.helpers.samplevnf_helper import OPNFVSampleVNF
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper
from yardstick.network_services.nfvi.resource import ResourceProfile
from yardstick.network_services.helpers.cpu import CpuSysCores

LOG = logging.getLogger(__name__)

# CGNAPT should work the same on all systems, we can provide the binary
CGNAPT_PIPELINE_COMMAND = \
    '{tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'
CGNAPT_CFG_CONFIG = "/tmp/cgnapt_config"
CGNAPT_CFG_SCRIPT = "/tmp/cgnapt_script"
DEFAULT_CONFIG_TPL_CFG = "cgnat.cfg"
APP_NAME = "vCGNAPT"
VNF_TYPE = "CGNAPT"
SW_DEFAULT_CORE = 6
HW_DEFAULT_CORE = 3
WAIT_FOR_STATIC_NAPT = 4


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
        self.deploy.deploy_vnfs(APP_NAME)

    def get_nfvi_type(self, scenario_cfg):
        return self.nfvi_context.get("context", 'baremetal')

    def instantiate(self, scenario_cfg, context_cfg):
        self.nfvi_context = \
            Context.get_context_from_server(scenario_cfg["nodes"][self.name])
        self.options = scenario_cfg["options"]
        self.nodes = scenario_cfg['nodes']
        self.vnf_cfg = \
            self.options[self.name].get('vnf_config',
                                        {'lb_config': 'SW',
                                         'lb_count': 1,
                                         'worker_config': '1C/1T',
                                         'worker_threads': 1})
        self.topology = scenario_cfg['topology']

        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)

        self.deploy = OPNFVSampleVNF(self.connection, self.bin_path)
        self.deploy_cgnapt_vnf()

        self.setup_vnf_environment(self.connection)
        interfaces = self.vnfd["vdu"][0]['external-interface']
        self.socket = \
            next((0 for v in interfaces
                  if v['virtual-interface']["vpci"][5] == "0"), 1)

        bound_pci = [v['virtual-interface']["vpci"] for v in interfaces]

        self.nfvi_type = self.get_nfvi_type(scenario_cfg)
        cores = self._validate_cpu_cfg(self.vnf_cfg)
        self.resource = ResourceProfile(mgmt_interface, interfaces, cores)

        self.connection.execute("pkill %s" % APP_NAME)
        self.dpdk_nic_bind = \
            provision_tool(self.connection,
                           os.path.join(self.bin_path, "dpdk_nic_bind.py"))
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
                    LOG.info("CGNAPT VNF is up and running.")
                    self._add_static_cgnat(self.nodes, interfaces)
                    queue_wrapper.clear()
                    self._resource_collect_start()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting VNF.")
            LOG.info("Waiting for CGNAPT VNF to start.. ")
            time.sleep(1)

    def terminate(self):
        self.execute_command("quit")
        self._vnf_process.terminate()
        self.connection.execute("pkill %s" % APP_NAME)
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

    def _get_random_public_pool_ip(self, ip):
        ip_addr = '.'.join(str(int(addr) + 1) if idx == 2 else addr for
                           idx, addr in enumerate(ip.split('.')))
        return ip_addr

    def _add_static_cgnat(self, nodes, interfaces):
        ip = "152.16.40.10"
        if self.options[self.name].get('napt', 'static') == 'static':
            gw_ips = self._get_cgnapt_config(interfaces)
            pipeline = SW_DEFAULT_CORE - 1
            if self.vnf_cfg.get("lb_config", "SW") == 'HW':
                pipeline = HW_DEFAULT_CORE
            for gw in gw_ips:
                cmd = "p {0} entry addm {1} 1 {2} 1 0 32 " \
                      "65535 65535 65535".format(pipeline, gw, ip)
                wt = int(self.vnf_cfg["worker_threads"])
                pipeline += \
                    wt + 3 if self.vnf_cfg.get("lb_config", "SW") == \
                    'HW' else wt
                ip = self._get_random_public_pool_ip(ip)
            self.execute_command(cmd)
            time.sleep(WAIT_FOR_STATIC_NAPT)

    def _get_cgnapt_config(self, interfaces):
        gateway_ips = []

        # fixme: Get private port and gateway from port list
        priv_ports = interfaces[::2]
        for interface in priv_ports:
            gateway_ips.append(self._get_ports_gateway(interface["name"]))
        return gateway_ips

    def _run_vcgnapt(self, filewrapper):
        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)
        interfaces = self.vnfd["vdu"][0]['external-interface']

        lb_count = self.vnf_cfg.get('lb_count', 3)
        lb_config = self.vnf_cfg.get('lb_config', 'SW')
        worker_config = self.vnf_cfg.get('worker_config', '1C/1T')
        worker_threads = self.vnf_cfg.get('worker_threads', 3)

        traffic_options = {}
        traffic_options['traffic_type'] = self.options.get('traffic_type', 4)
        traffic_options['pkt_type'] = \
            'ipv%s' % self.options.get("traffic_type", 4)

        traffic_options['vnf_type'] = VNF_TYPE
        multiport = MultiPortConfig(self.topology,
                                    DEFAULT_CONFIG_TPL_CFG,
                                    posixpath.basename(CGNAPT_CFG_CONFIG),
                                    interfaces,
                                    VNF_TYPE,
                                    lb_count,
                                    worker_threads,
                                    worker_config,
                                    lb_config,
                                    self.socket)

        multiport.generate_config()
        new_config = \
            self._append_routes(open(CGNAPT_CFG_CONFIG, 'r').read())
        new_config = self._append_nd_routes(new_config)
        new_config = self._update_traffic_type(new_config, traffic_options)
        new_config = self._update_packet_type(new_config, traffic_options)

        self._provide_config_file(
            posixpath.basename(CGNAPT_CFG_CONFIG), new_config)

        self._provide_config_file(posixpath.basename(CGNAPT_CFG_SCRIPT),
                                  multiport.generate_script(self.vnfd))

        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path,
                                                APP_NAME))
        ports_len = len(multiport.port_pair_list) * 2
        ports_len_hex = hex(
            eval('0b' + "".join([str(1) for x in range(ports_len)])))
        cmd = CGNAPT_PIPELINE_COMMAND.format(cfg_file=CGNAPT_CFG_CONFIG,
                                             script=CGNAPT_CFG_SCRIPT,
                                             ports_len_hex=ports_len_hex,
                                             tool_path=tool_path)
        self.connection.run(cmd, stdin=filewrapper, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    def _get_cpu_sibling_list(self, cores):
        try:
            cpu_topo = []
            for core in cores:
                sys_path = "/sys/devices/system/cpu/"
                sys_cmd = \
                    "%s/cpu%s/topology/thread_siblings_list" \
                    % (sys_path, core)
                cpuid = \
                    self.connection.execute("awk -F: '{ print $1 }' < %s" %
                                            sys_cmd)[1]
                cpu_topo += \
                    [(idx) if idx.isdigit() else idx for
                     idx in cpuid.split(',')]

            return [cpu.strip() for cpu in cpu_topo]
        except Exception:
            return []

    def _validate_cpu_cfg(self, vnf_cfg):
        sysObj = CpuSysCores(self.connection)
        self.sys_cpu = sysObj.get_core_socket()
        if vnf_cfg.get("lb_config", "SW") == 'HW':
            num_core = HW_DEFAULT_CORE + int(vnf_cfg["worker_threads"])
        else:
            num_core = SW_DEFAULT_CORE + int(vnf_cfg["worker_threads"])
        app_cpu = self.sys_cpu[str(self.socket)][:num_core]
        return self._get_cpu_sibling_list(app_cpu)

    def _provide_config_file(self, prefix, template, vars={}):
        cfg, cfg_content = tempfile.mkstemp()
        cfg = os.fdopen(cfg, "w+")
        cfg.write(template.format(**vars))
        cfg.close()
        cfg_file = os.path.join("/tmp", prefix)
        self.connection.put(cfg_content, cfg_file)
        return cfg_file

    def execute_command(self, cmd):
        LOG.info("CGNAPT command: %s", cmd)
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

        LOG.debug("CGNAPT collect KPIs {0}".format(result))
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
