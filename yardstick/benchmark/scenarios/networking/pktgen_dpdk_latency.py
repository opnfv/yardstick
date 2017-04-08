##############################################################################
# Copyright (c) 2016 ZTE corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import pkg_resources
import logging
import time

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class PktgenDPDKLatency(base.Scenario):
    """Execute pktgen-dpdk on one vm and execute testpmd on the other vm

  Parameters
    packetsize - packet size in bytes without the CRC
        type:    int
        unit:    bytes
        default: 64
    """
    __scenario_type__ = "PktgenDPDKLatency"

    PKTGEN_DPDK_SCRIPT = 'pktgen_dpdk_latency_benchmark.bash'
    TESTPMD_SCRIPT = 'testpmd_fwd.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.pktgen_dpdk_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            PktgenDPDKLatency.PKTGEN_DPDK_SCRIPT)
        self.testpmd_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            PktgenDPDKLatency.TESTPMD_SCRIPT)
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
        self.server._put_file_shell(self.testpmd_script, '~/testpmd_fwd.sh')

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip,
                              key_filename=host_key_filename,
                              port=host_ssh_port)
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(
            self.pktgen_dpdk_script, '~/pktgen_dpdk.sh')

        self.setup_done = True
        self.testpmd_args = ''
        self.pktgen_args = []

    @staticmethod
    def get_port_mac(sshclient, port):
        cmd = "ifconfig |grep HWaddr |grep %s |awk '{print $5}' " % port
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = sshclient.execute(cmd)

        if status:
            raise RuntimeError(stderr)
        else:
            return stdout.rstrip()

    @staticmethod
    def get_port_ip(sshclient, port):
        cmd = "ifconfig %s |grep 'inet addr' |awk '{print $2}' \
            |cut -d ':' -f2 " % port
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = sshclient.execute(cmd)

        if status:
            raise RuntimeError(stderr)
        else:
            return stdout.rstrip()

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        if not self.testpmd_args:
            self.testpmd_args = self.get_port_mac(self.client, 'eth2')

        if not self.pktgen_args:
            server_rev_mac = self.get_port_mac(self.server, 'eth1')
            server_send_mac = self.get_port_mac(self.server, 'eth2')
            client_src_ip = self.get_port_ip(self.client, 'eth1')
            client_dst_ip = self.get_port_ip(self.client, 'eth2')

            self.pktgen_args = [client_src_ip, client_dst_ip,
                                server_rev_mac, server_send_mac]

        options = self.scenario_cfg['options']
        packetsize = options.get("packetsize", 64)
        rate = options.get("rate", 100)

        cmd = "screen sudo -E bash ~/testpmd_fwd.sh %s " % (self.testpmd_args)
        LOG.debug("Executing command: %s", cmd)
        self.server.send_command(cmd)

        time.sleep(1)

        cmd = "screen sudo -E bash ~/pktgen_dpdk.sh %s %s %s %s %s %s" % \
            (self.pktgen_args[0], self.pktgen_args[1], self.pktgen_args[2],
             self.pktgen_args[3], rate, packetsize)
        LOG.debug("Executing command: %s", cmd)
        self.client.send_command(cmd)

        # wait for finishing test
        time.sleep(1)

        cmd = "cat ~/result.log -vT \
               |awk '{match($0,/\[8;40H +[0-9]+/)} \
               {print substr($0,RSTART,RLENGTH)}' \
               |grep -v ^$ |awk '{if ($2 != 0) print $2}'"
        client_status, client_stdout, client_stderr = self.client.execute(cmd)

        if client_status:
            raise RuntimeError(client_stderr)

        avg_latency = 0
        if client_stdout:
            latency_list = client_stdout.split('\n')[0:-2]
            LOG.info("10 samples of latency: %s", latency_list)
            latency_sum = 0
            for i in latency_list:
                latency_sum += int(i)
            avg_latency = latency_sum / len(latency_list)

        result.update({"avg_latency": avg_latency})

        if avg_latency and "sla" in self.scenario_cfg:
            sla_max_latency = int(self.scenario_cfg["sla"]["max_latency"])
            LOG.info("avg_latency : %d ", avg_latency)
            LOG.info("sla_max_latency: %d", sla_max_latency)
            debug_info = "avg_latency %d > sla_max_latency %d" \
                % (avg_latency, sla_max_latency)
            assert avg_latency <= sla_max_latency, debug_info
