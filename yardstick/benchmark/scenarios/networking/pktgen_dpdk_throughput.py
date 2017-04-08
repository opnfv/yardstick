##############################################################################
# Copyright (c) 2017 Nokia and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import pkg_resources
import logging
import json
import time

import yardstick.ssh as ssh
import yardstick.common.utils as utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class PktgenDPDK(base.Scenario):
    """Execute pktgen-dpdk on one vm and execute testpmd on the other vm
    """
    __scenario_type__ = "PktgenDPDK"

    PKTGEN_DPDK_SCRIPT = 'pktgen_dpdk_benchmark.bash'
    TESTPMD_SCRIPT = 'testpmd_rev.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.source_ipaddr = [None] * 2
        self.source_ipaddr[0] = \
            self.context_cfg["host"].get("ipaddr", '127.0.0.1')
        self.target_ipaddr = [None] * 2
        self.target_ipaddr[0] = \
            self.context_cfg["target"].get("ipaddr", '127.0.0.1')
        self.target_macaddr = [None] * 2
        self.setup_done = False
        self.dpdk_setup_done = False

    def setup(self):
        """scenario setup"""

        self.pktgen_dpdk_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            PktgenDPDK.PKTGEN_DPDK_SCRIPT)
        self.testpmd_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            PktgenDPDK.TESTPMD_SCRIPT)

        host = self.context_cfg['host']
        host_user = host.get('user', 'ubuntu')
        host_ssh_port = host.get('ssh_port', ssh.DEFAULT_PORT)
        host_ip = host.get('ip', None)
        host_key_filename = host.get('key_filename', '~/.ssh/id_rsa')
        target = self.context_cfg['target']
        target_user = target.get('user', 'ubuntu')
        target_ssh_port = target.get('ssh_port', ssh.DEFAULT_PORT)
        target_ip = target.get('ip', None)
        target_key_filename = target.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, target:%s", target_user, target_ip)
        self.server = ssh.SSH(target_user, target_ip,
                              key_filename=target_key_filename,
                              port=target_ssh_port)
        self.server.wait(timeout=600)

        # copy script to host
        self.server._put_file_shell(self.testpmd_script, '~/testpmd_rev.sh')

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip,
                              key_filename=host_key_filename,
                              port=host_ssh_port)
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(self.pktgen_dpdk_script,
                                    '~/pktgen_dpdk.sh')

        self.setup_done = True

    def dpdk_setup(self):
        """dpdk setup"""

        # disable Address Space Layout Randomization (ASLR)
        cmd = "echo 0 | sudo tee /proc/sys/kernel/randomize_va_space"
        self.server.send_command(cmd)
        self.client.send_command(cmd)

        if not self._is_dpdk_setup("client"):
            cmd = "sudo ifup eth1"
            LOG.debug("Executing command: %s", cmd)
            self.client.send_command(cmd)
            time.sleep(1)
            self.source_ipaddr[1] = utils.get_port_ip(self.client, 'eth1')
            self.client.run("tee ~/.pktgen-dpdk.ipaddr.eth1 > /dev/null",
                            stdin=self.source_ipaddr[1])
        else:
            cmd = "cat ~/.pktgen-dpdk.ipaddr.eth1"
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.source_ipaddr[1] = stdout

        if not self._is_dpdk_setup("server"):
            cmd = "sudo ifup eth1"
            LOG.debug("Executing command: %s", cmd)
            self.server.send_command(cmd)
            time.sleep(1)
            self.target_ipaddr[1] = utils.get_port_ip(self.server, 'eth1')
            self.target_macaddr[1] = utils.get_port_mac(self.server, 'eth1')
            self.server.run("tee ~/.testpmd.ipaddr.eth1 > /dev/null",
                            stdin=self.target_ipaddr[1])
            self.server.run("tee ~/.testpmd.macaddr.eth1 > /dev/null",
                            stdin=self.target_macaddr[1])

            cmd = "screen sudo -E bash ~/testpmd_rev.sh"
            LOG.debug("Executing command: %s", cmd)
            self.server.send_command(cmd)

            time.sleep(1)
        else:
            cmd = "cat ~/.testpmd.ipaddr.eth1"
            status, stdout, stderr = self.server.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.target_ipaddr[1] = stdout

            cmd = "cat ~/.testpmd.macaddr.eth1"
            status, stdout, stderr = self.server.execute(cmd)
            if status:
                raise RuntimeError(stderr)
            self.target_macaddr[1] = stdout

        self.dpdk_setup_done = True

    def _is_dpdk_setup(self, host):
        """Is dpdk already setup in the host?"""
        is_run = True
        cmd = "ip a | grep eth1 2>/dev/null"
        LOG.debug("Executing command: %s in %s", cmd, host)
        if "server" in host:
            status, stdout, stderr = self.server.execute(cmd)
            if stdout:
                is_run = False
        else:
            status, stdout, stderr = self.client.execute(cmd)
            if stdout:
                is_run = False

        return is_run

    def _dpdk_get_result(self):
        """Get packet statistics from server"""
        cmd = "sudo /dpdk/destdir/bin/dpdk-procinfo -- --stats 2>/dev/null | \
              awk '$1 ~ /RX-packets/' | cut -d ':' -f2  | cut -d ' ' -f2 | \
              head -n 1"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        received = int(stdout)

        cmd = "sudo /dpdk/destdir/bin/dpdk-procinfo -- --stats-reset" \
            " > /dev/null 2>&1"
        self.server.execute(cmd)
        time.sleep(1)
        self.server.execute(cmd)
        return received

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        if not self.dpdk_setup_done:
            self.dpdk_setup()

        options = self.scenario_cfg['options']
        packetsize = options.get("packetsize", 60)
        rate = options.get("rate", 100)
        self.number_of_ports = options.get("number_of_ports", 10)
        # if run by a duration runner
        duration_time = self.scenario_cfg["runner"].get("duration", None) \
            if "runner" in self.scenario_cfg else None
        # if run by an arithmetic runner
        arithmetic_time = options.get("duration", None)

        if duration_time:
            duration = duration_time
        elif arithmetic_time:
            duration = arithmetic_time
        else:
            duration = 20

        cmd = "sudo bash pktgen_dpdk.sh %s %s %s %s %s %s %s" \
            % (self.source_ipaddr[1],
               self.target_ipaddr[1], self.target_macaddr[1],
               self.number_of_ports, packetsize, duration, rate)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))

        result['packets_received'] = self._dpdk_get_result()

        result['packetsize'] = packetsize

        if "sla" in self.scenario_cfg:
            sent = result['packets_sent']
            received = result['packets_received']
            ppm = 1000000 * (sent - received) / sent
            # Added by Jing
            ppm += (sent - received) % sent > 0
            LOG.debug("Lost packets %d - Lost ppm %d", (sent - received), ppm)
            sla_max_ppm = int(self.scenario_cfg["sla"]["max_ppm"])
            assert ppm <= sla_max_ppm, "ppm %d > sla_max_ppm %d; " \
                % (ppm, sla_max_ppm)
