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
import yardstick.common.utils as utils
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
        target = self.context_cfg['target']
        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(target, defaults={"user": "ubuntu"})
        self.server.wait(timeout=600)

        # copy script to host
        self.server._put_file_shell(self.testpmd_script, '~/testpmd_fwd.sh')

        LOG.info("user:%s, host:%s", host['user'], host['ip'])
        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(
            self.pktgen_dpdk_script, '~/pktgen_dpdk.sh')

        self.setup_done = True
        self.testpmd_args = ''
        self.pktgen_args = []

    def run(self, result):
        """execute the benchmark"""

        options = self.scenario_cfg['options']
        eth1 = options.get("eth1", "ens4")
        eth2 = options.get("eth2", "ens5")
        if not self.setup_done:
            self.setup()

        if not self.testpmd_args:
            self.testpmd_args = utils.get_port_mac(self.client, eth2)

        if not self.pktgen_args:
            server_rev_mac = utils.get_port_mac(self.server, eth1)
            server_send_mac = utils.get_port_mac(self.server, eth2)
            client_src_ip = utils.get_port_ip(self.client, eth1)
            client_dst_ip = utils.get_port_ip(self.client, eth2)

            self.pktgen_args = [client_src_ip, client_dst_ip,
                                server_rev_mac, server_send_mac]

        packetsize = options.get("packetsize", 64)
        rate = options.get("rate", 100)

        cmd = "screen sudo -E bash ~/testpmd_fwd.sh %s %s %s" % \
            (self.testpmd_args, eth1, eth2)
        LOG.debug("Executing command: %s", cmd)
        self.server.send_command(cmd)

        time.sleep(1)

        cmd = "screen sudo -E bash ~/pktgen_dpdk.sh %s %s %s %s %s %s %s %s" % \
            (self.pktgen_args[0], self.pktgen_args[1], self.pktgen_args[2],
             self.pktgen_args[3], rate, packetsize, eth1, eth2)
        LOG.debug("Executing command: %s", cmd)
        self.client.send_command(cmd)

        # wait for finishing test
        time.sleep(60)

        cmd = r"""\
cat ~/result.log -vT \
|awk '{match($0,/\[8;40H +[0-9]+/)} \
{print substr($0,RSTART,RLENGTH)}' \
|grep -v ^$ |awk '{if ($2 != 0) print $2}'\
"""
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
