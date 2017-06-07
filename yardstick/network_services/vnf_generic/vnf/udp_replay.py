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
from multiprocessing import Queue
import multiprocessing
import time
import os
import logging
import re

from yardstick import ssh
from yardstick.network_services.utils import provision_tool
from yardstick.benchmark.contexts.base import Context
from yardstick.network_services.helpers.samplevnf_helper import OPNFVSampleVNF
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.base import QueueFileWrapper

LOG = logging.getLogger(__name__)

# UDP_Replay should work the same on all systems, we can provide the binary
REPLAY_PIPELINE_COMMAND = \
    '{tool_path} -c {cpu_mask_hex} -n 4 -w {whitelist} -- ' \
    '{hw_csum} -p {ports_len_hex} --config="{config}"'

# {tool_path} -p {ports_len_hex} -f {cfg_file} -s {script}'
APP_NAME = "UDP_Replay"


class UdpReplayApproxVnf(GenericVNF):

    def __init__(self, vnfd):
        super(UdpReplayApproxVnf, self).__init__(vnfd)
        self.socket = None
        self.q_in = Queue()
        self.q_out = Queue()
        self.vnf_cfg = None
        self._vnf_process = None
        self.connection = None
        self.my_ports = None
        self.resource = None

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
        super(UdpReplayApproxVnf, self).scale(flavor)

    def deploy_udp_replay_vnf(self):
        self.deploy.deploy_vnfs(APP_NAME)

    def get_nfvi_type(self, scenario_cfg):
        return self.nfvi_context.get("context", 'baremetal')

    def instantiate(self, scenario_cfg, context_cfg):
        self.nfvi_context = \
            Context.get_context_from_server(scenario_cfg["nodes"][self.name])
        self.options = scenario_cfg["options"]
        self.nodes = scenario_cfg['nodes']
        self.topology = scenario_cfg['topology']

        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)

        self.my_ports = self.get_my_ports()
        self.deploy = OPNFVSampleVNF(self.connection, self.bin_path)
        self.deploy_udp_replay_vnf()

        self.setup_vnf_environment(self.connection)
        self.interfaces = self.vnfd["vdu"][0]['external-interface']
        self.socket = \
            next((0 for v in self.interfaces
                  if v['virtual-interface']["vpci"][5] == "0"), 1)

        bound_pci = [v['virtual-interface']["vpci"] for v in self.interfaces]

        self.nfvi_type = self.get_nfvi_type(scenario_cfg)

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
        queue_wrapper = QueueFileWrapper(self.q_in, self.q_out, "Replay>")
        self._vnf_process = \
            multiprocessing.Process(target=self._run_udp_replay,
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
                if "Replay>" in message:
                    LOG.info("UDP Replay VNF is up and running.")
                    queue_wrapper.clear()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting VNF.")
            LOG.info("Waiting for UDP Replay VNF to start.. ")
            time.sleep(1)
        return self._vnf_process.is_alive()

    def terminate(self):
        self.execute_command("quit")
        self._vnf_process.terminate()
        self.connection.execute("pkill %s" % APP_NAME)
        for vpci, driver in self.used_drivers.items():
            self.connection.execute(
                "{dpdk_nic_bind} --force  -b {driver}"
                " {vpci}".format(vpci=vpci, driver=driver,
                                 dpdk_nic_bind=self.dpdk_nic_bind))

    def get_my_ports(self):
        self.generate_port_pairs(self.topology)
        self.priv_ports = [int(x[0][-1]) for x in self.tg_port_pairs]
        self.pub_ports = [int(x[1][-1]) for x in self.tg_port_pairs]
        my_ports = list(set(self.priv_ports).union(set(self.pub_ports)))
        return my_ports

    def _run_udp_replay(self, filewrapper):
        mgmt_interface = self.vnfd["mgmt-interface"]
        self.connection = ssh.SSH.from_node(mgmt_interface)

        traffic_options = {}
        traffic_options['traffic_type'] = self.options.get('traffic_type', 4)
        traffic_options['pkt_type'] = \
            'ipv%s' % self.options.get("traffic_type", 4)

        tool_path = provision_tool(self.connection,
                                   os.path.join(self.bin_path,
                                                APP_NAME))
        ports_len = len(self.my_ports)
        ports_len_hex = hex(
            eval('0b' + "".join([str(1) for x in range(ports_len)])))
        cpu_mask_hex = hex(
            eval('0b' + "".join([str(1) for x in range(ports_len + 1)])))
        mask = [0]
        config = []
        for port in self.my_ports:
            temp = mask[:]
            temp.insert(0, port)
            temp.append(sum([port, 1]))
            config.append(temp)
        config_value = "".join([str(tuple(x)) for x in config])

        hw_csum = "--no-hw-csum"
        if self.nfvi_type in ('baremetal', 'sriov'):
            hw_csum = ""

        whitelist = " -w ".join([v['virtual-interface']["vpci"] for v in
                                self.interfaces])
        cmd = REPLAY_PIPELINE_COMMAND.format(ports_len_hex=ports_len_hex,
                                             tool_path=tool_path,
                                             hw_csum=hw_csum,
                                             whitelist=whitelist,
                                             cpu_mask_hex=cpu_mask_hex,
                                             config=config_value)
        LOG.debug(cmd)
        self.connection.run(cmd, stdin=filewrapper, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    def execute_command(self, cmd):
        LOG.info("UDP replay command: %s", cmd)
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
        stats = self.get_stats_udp_replay()
        udpreplay = stats.split()
        index = udpreplay.index('0')
        split_stats = stats.split()[index:]
        ports = len(self.my_ports) * 5
        split_stats = split_stats[:ports]
        result["packets_in"] = result.get(
            "packets_in", 0) + sum(int(i) for i in split_stats[1::5])
        result["packets_fwd"] = result.get(
            "packets_fwd", 0) + sum(int(i) for i in split_stats[2::5])
        result["packets_dropped"] = result.get(
            "packets_dropped", 0) + sum(int(i) for i in split_stats[3::5]) + \
            sum(int(i) for i in split_stats[4::5])

        LOG.debug("UDP Replay collect KPIs {0}".format(result))
        return result

    def get_stats_udp_replay(self):
        """
        Method for checking the statistics

        :return:
           UDP Replay statistics
        """
        cmd = 'UDP_Replay stats'
        out = self.execute_command(cmd)
        return out
