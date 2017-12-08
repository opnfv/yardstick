# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" VsperfDPDK specific scenario definition """

from __future__ import absolute_import
import pkg_resources
import logging
import subprocess
import time
import re
import json

import yardstick.ssh as ssh
import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class MoongenTestPMD(base.Scenario):
    """Execute vsperf with defined parameters

  Parameters:
    frame_size - a frame size for which test should be executed;
        Multiple frame sizes can be tested by modification of sequence runner
        section inside TC YAML definition.
        type:    string
        default: "64"
    multistream - the number of simulated streams
        type:    string
        default: 0 (disabled)
    testpmd_queue - specifies how many queues you will use the VM
                    only useful when forward_type is true.
        type:    int
        default: 1(one queue)
    trafficgen_port1 - specifies device name of 1st interface connected to
        the trafficgen
        type:   string
        default: NA
    trafficgen_port2 - specifies device name of 2nd interface connected to
        the trafficgen
        type:   string
        default: NA
    moongen_host_user - specifies moongen host ssh user name
        type: string
        default: root
    moongen_host_passwd - specifies moongen host ssh user password
        type: string
        default: root
    moongen_host_ip - specifies moongen host ssh ip address
        type: string
        default NA
    moongen_dir - specifies where is the moongen installtion dir
        type: string
        default NA
    moongen_runBidirec - specifies moongen will run in one traffic
                         or two traffic.
        type: string
        default true
    Package_Loss - specifies the package_Loss number in moongen server.
        type: int
        default 0(0%)
    SearchRuntime - specifies the SearchRuntime and validation time
                    on moongen server.
        type: int
        default 60(s)
    moongen_port1_mac - moongen server port1 mac address.
        type: string
        default NA
    moongen_port2_mac - moongen server port2 mac address.
        type: string
        default NA
    forward_type - VM forward type is l2fwd or testpmd.
        type: string
        default: testpmd
    """
    __scenario_type__ = "MoongenTestPMD"

    TESTPMD_SCRIPT = 'moongen_testpmd.bash'
    VSPERF_CONFIG = '/tmp/opnfv-vsperf-cfg.lua'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.forward_setup_done = False
        self.moongen_host_user = \
            scenario_cfg['options'].get('moongen_host_user', "root")
        self.moongen_host_passwd = \
            scenario_cfg['options'].get('moongen_host_passwd', "r00t")
        self.moongen_dir = \
            scenario_cfg['options'].get('moongen_dir', '~/moongen.py')
        self.testpmd_queue = \
            scenario_cfg['options'].get('testpmd_queue', 1)
        self.moongen_host_ip = \
            scenario_cfg['options'].get('moongen_host_ip', "127.0.0.1")
        self.moongen_port1_mac = \
            scenario_cfg['options'].get('moongen_port1_mac', None)
        self.moongen_port2_mac = \
            scenario_cfg['options'].get('moongen_port2_mac', None)
        self.tg_port1 = \
            self.scenario_cfg['options'].get('trafficgen_port1', "enp2s0f0")
        self.tg_port2 = \
            self.scenario_cfg['options'].get('trafficgen_port2', "enp2s0f1")
        self.forward_type = \
            self.scenario_cfg['options'].get('forward_type', 'testpmd')
        self.tgen_port1_mac = None
        self.tgen_port2_mac = None

    def setup(self):
        """scenario setup"""
        host = self.context_cfg['host']

        task_id = self.scenario_cfg['task_id']
        context_number = task_id.split('-')[0]
        self.tg_port1_nw = 'demo' + \
            "-" + context_number + "-" + \
            self.scenario_cfg['options'].get('trafficgen_port1_nw', 'test2')
        self.tg_port2_nw = 'demo' + \
            "-" + context_number + "-" + \
            self.scenario_cfg['options'].get('trafficgen_port2_nw', 'test3')

        # copy vsperf conf to VM
        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        # traffic generation could last long
        self.client.wait(timeout=1800)

        self.server = ssh.SSH(
            self.moongen_host_user,
            self.moongen_host_ip,
            password=self.moongen_host_passwd
        )
        # traffic generation could last long
        self.server.wait(timeout=1800)

        self.setup_done = True

    def forward_setup(self):
        """forward tool setup"""

        # setup forward loopback in VM
        self.testpmd_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            self.TESTPMD_SCRIPT)

        self.client._put_file_shell(self.testpmd_script,
                                    '~/testpmd_vsperf.sh')

        # disable Address Space Layout Randomization (ASLR)
        cmd = "echo 0 | sudo tee /proc/sys/kernel/randomize_va_space"
        self.client.send_command(cmd)

        if not self._is_forward_setup():
            self.tgen_port1_ip = \
                utils.get_port_ip(self.client, self.tg_port1)
            self.tgen_port1_mac = \
                utils.get_port_mac(self.client, self.tg_port1)
            self.client.run("tee ~/.testpmd.ipaddr.port1 > /dev/null",
                            stdin=self.tgen_port1_ip)
            self.client.run("tee ~/.testpmd.macaddr.port1 > /dev/null",
                            stdin=self.tgen_port1_mac)
            self.tgen_port2_ip = \
                utils.get_port_ip(self.client, self.tg_port2)
            self.tgen_port2_mac = \
                utils.get_port_mac(self.client, self.tg_port2)
            self.client.run("tee ~/.testpmd.ipaddr.port2 > /dev/null",
                            stdin=self.tgen_port2_ip)
            self.client.run("tee ~/.testpmd.macaddr.port2 > /dev/null",
                            stdin=self.tgen_port2_mac)
        else:
            cmd = "cat ~/.testpmd.macaddr.port1"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.tgen_port1_mac = stdout
            cmd = "cat ~/.testpmd.ipaddr.port1"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.tgen_port1_ip = stdout
            cmd = "cat ~/.testpmd.macaddr.port2"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.tgen_port2_mac = stdout
            cmd = "cat ~/.testpmd.ipaddr.port2"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.tgen_port2_ip = stdout

        LOG.info("forward type is %s", self.forward_type)
        if self.forward_type == 'testpmd':
            cmd = "sudo ip link set %s down" % (self.tg_port1)
            LOG.debug("Executing command: %s", cmd)
            self.client.execute(cmd)
            cmd = "sudo ip link set %s down" % (self.tg_port2)
            LOG.debug("Executing command: %s", cmd)
            self.client.execute(cmd)
            cmd = "screen -d -m sudo -E bash ~/testpmd_vsperf.sh %s %s %d" % \
                (self.moongen_port1_mac, self.moongen_port2_mac,
                 self.testpmd_queue)
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

        elif self.forward_type == 'l2fwd':
            cmd = ('sed -i "s/static char \*net1 = \\\"eth1\\\";'
                   '/static char \*net1 = \\\"%s %s %s\\\";/g" /home/l2fwd/l2fwd.c'
                   % (self.tg_port1, self.tgen_port1_ip, self.moongen_port1_mac))
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)

            cmd = ('sed -i "s/static char \*net2 = \\\"eth2\\\";'
                   '/static char \*net2 = \\\"%s %s %s\\\";/g" /home/l2fwd/l2fwd.c'
                   % (self.tg_port2, self.tgen_port2_ip, self.moongen_port2_mac))
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)

            cmd = ('cd /home/l2fwd/;make;./gen_debian_package.sh;'
                   'sudo dpkg -i *.deb;'
                   'sudo modprobe l2fwd')
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)

        time.sleep(1)

        self.forward_setup_done = True

    def _is_forward_setup(self):
        """Is forward already setup in the host?"""
        if self.forward_type is 'testpmd':
            is_run = True
            cmd = "ip a | grep %s 2>/dev/null" % (self.tg_port1)
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if stdout:
                is_run = False
            return is_run
        elif self.forward_type is 'l2fwd':
            cmd = ('sudo lsmod |grep l2fwd')
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if stdout:
                return True
            else:
                return False

    def generate_config_file(self, frame_size, traffic_type, multistream,
                             runBidirec, tg_port1_vlan, tg_port2_vlan,
                             SearchRuntime, Package_Loss):
        out_text = """\
VSPERF {
testType = 'throughput',
nrFlows = %d,
runBidirec = %s,
frameSize = %d,
srcMacs = {\'%s\', \'%s\'},
dstMacs = {\'%s\', \'%s\'},
vlanIds = {%d, %d},
searchRunTime = %d,
validationRunTime = %d,
acceptableLossPct = %d,
ports = {0,1},
}
""" % (multistream, runBidirec, frame_size, self.moongen_port1_mac,
       self.moongen_port2_mac, self.tgen_port1_mac, self.tgen_port2_mac,
       tg_port1_vlan, tg_port2_vlan, SearchRuntime, SearchRuntime, Package_Loss)
        with open(self.VSPERF_CONFIG, "wt") as out_file:
           out_file.write(out_text)
        self.CONFIG_FILE=True

    def result_to_data(self, result, frame_size):
        search_pattern = re.compile(
            r'\[REPORT\]\s+total\:\s+'
            r'Tx\s+frames\:\s+(\d+)\s+'
            r'Rx\s+Frames\:\s+(\d+)\s+'
            r'frame\s+loss\:\s+(\d+)\,'
            r'\s+(\d+\.\d+|\d+)%\s+'
            r'Tx\s+Mpps\:\s+(\d+.\d+|\d+)\s+'
            r'Rx\s+Mpps\:\s+(\d+\.\d+|\d+)',
            re.IGNORECASE)
        results_match = search_pattern.search(result)
        if results_match:
            rx_mpps = float(results_match.group(6))
            tx_mpps = float(results_match.group(5))
        else:
            rx_mpps = 0
            tx_mpps = 0
        test_result = {"rx_mpps": rx_mpps, "tx_mpps": tx_mpps}
        self.TO_DATA=True
        return test_result

    def run(self, result):
        """ execute the vsperf benchmark and return test results
            within result dictionary
        """

        if not self.setup_done:
            self.setup()

        # get vsperf options
        options = self.scenario_cfg['options']
        traffic_type = self.scenario_cfg['options'].\
            get("traffic_type", "rfc2544_throughput")
        multistream = self.scenario_cfg['options'].get("multistream", 1)

        if not self.forward_setup_done:
            self.forward_setup()

        if 'frame_size' in options:
            frame_size = self.scenario_cfg['options'].get("frame_size", 64)
        Package_Loss = self.scenario_cfg['options'].get("Package_Loss", 0)
        runBidirec = self.scenario_cfg['options'].get("moongen_runBidirec",
                                                      "true")
        SearchRuntime = self.scenario_cfg['options'].get("SearchRuntime", 10)

        cmd = "openstack network show %s --format json -c " \
              "provider:segmentation_id" % (self.tg_port1_nw)
        LOG.debug("Executing command: %s", cmd)
        output = subprocess.check_output(cmd, shell=True)
        try:
            tg_port1_vlan = json.loads(output).get("provider:segmentation_id", 1)
        except TypeError:
            tg_port1_vlan = 1

        cmd = "openstack network show %s --format json -c " \
              "provider:segmentation_id" % (self.tg_port2_nw)
        LOG.debug("Executing command: %s", cmd)
        output = subprocess.check_output(cmd, shell=True)
        try:
            tg_port1_vlan = json.loads(output).get("provider:segmentation_id", 2)
        except TypeError:
            tg_port1_vlan = 2

        self.generate_config_file(frame_size, traffic_type, multistream,
                                  runBidirec, tg_port1_vlan,
                                  tg_port2_vlan, SearchRuntime, Package_Loss)

        self.server.execute("rm -f %s/opnfv-vsperf-cfg.lua" %
                            (self.moongen_dir))
        self.server._put_file_shell(self.VSPERF_CONFIG,
                                    "%s/opnfv-vsperf-cfg.lua"
                                    % (self.moongen_dir))

        # execute moongen
        cmd = ("cd %s;./MoonGen/build/MoonGen ./trafficgen.lua"
               % (self.moongen_dir))
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        moongen_result = self.result_to_data(stdout, frame_size)
        LOG.info(moongen_result)
        result.update(moongen_result)

        if "sla" in self.scenario_cfg:
            throughput_rx_mpps = int(
                self.scenario_cfg["sla"]["throughput_rx_mpps"])

            assert throughput_rx_mpps <= moongen_result["tx_mpps"], \
                "sla_throughput_rx_mpps %f > throughput_rx_mpps(%f); " % \
                (throughput_rx_mpps, moongen_result["tx_mpps"])

    def teardown(self):
        """cleanup after the test execution"""

        # execute external setup script
        self.setup_done = False

