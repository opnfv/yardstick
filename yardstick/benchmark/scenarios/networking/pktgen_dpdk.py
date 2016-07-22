##############################################################################
# Copyright (c) 2016 ZTE corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import logging
import json
import time

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
from yardstick.benchmark.contexts.base import Context

LOG = logging.getLogger(__name__)


class PktgenDPDKLatency(base.Scenario):
    """Execute pktgen-dpdk on one vm and execute testpmd on the other vm

  Parameters
    packetsize - packet size in bytes without the CRC
        type:    int
        unit:    bytes
        default: 60
    """
    __scenario_type__ = "PktgenDPDKLatency"

    PKTGEN_DPDK_SCRIPT = 'pktgen_dpdk_latency_benchmark.bash'
    TESTPMD_SCRIPT = 'testpmd_fwd.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.pktgen_dpdk_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            PktgenDPDKLatency.PKTGEN_DPDK_SCRIPT)
        self.testpmd_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            PktgenDPDKLatency.TESTPMD_SCRIPT)
        host = self.context_cfg['host']
        host_user = host.get('user', 'ubuntu')
        host_ip = host.get('ip', None)
        host_key_filename = host.get('key_filename', '~/.ssh/id_rsa')
        target = self.context_cfg['target']
        target_user = target.get('user', 'ubuntu')
        target_ip = target.get('ip', None)
        target_key_filename = target.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, target:%s", target_user, target_ip)
        self.server = ssh.SSH(target_user, target_ip,
                              key_filename=target_key_filename)
        self.server.wait(timeout=600)

        # copy script to host
        self.server.run("cat > ~/testpmd.sh",
                        stdin=open(self.testpmd_script, "rb"))

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip,
                              key_filename=host_key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/pktgen_dpdk.sh",
                        stdin=open(self.pktgen_dpdk_script, "rb"))

        self.setup_done = True

    def get_server_mac(self, port):
        cmd = "ifconfig %s |grep HWaddr |awk '{print $5}' " % port
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)

        if status:
            raise RuntimeError(stderr)
        else:
           return stdout

    def get_client_mac(self, port):
        cmd = "ifconfig %s |grep HWaddr |awk '{print $5}' " % port
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)
        else:
           return stdout

    def get_client_ip(self, port):
        cmd = "ifconfig %s |grep 'inet addr' |awk '{print $2}' \
            |cut -d ':' -f2 " % port
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)
        else:
           return stdout

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        packetsize = options.get("packetsize", 60)
        rate = options.get("rate", 100)
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

        server_rev_mac = self.get_server_mac('eth1')
        server_send_mac = self.get_server_mac('eth2')

        client_src_ip = self.get_client_ip('eth1')
        client_dst_ip = self.get_client_ip('eth2')
        client_dst_mac = self.get_client_mac('eth2')

        cmd = "sudo bash testpmd.sh %s " % (client_dst_mac)
        LOG.debug("Executing command: %s", cmd)
        server_status, server_stdout, server_stderr = self.server.execute(cmd)

        if server_status:
            raise RuntimeError(server_stderr)

        sleep(10)

        cmd = "sudo bash pktgen_dpdk.sh" \
            % (client_src_ip, client_dst_ip, server_rev_mac, server_send_mac, \
                rate, packetsize)
        LOG.debug("Executing command: %s", cmd)
        client_status, client_stdout, client_stderr = self.client.execute(cmd)

        if client_status:
            raise RuntimeError(client_stderr)

        LOG.debug("client_stdout : %s" % client_stdout)

        result.update(json.loads(client_stdout))

        if "sla" in self.scenario_cfg:
            # TODO: get the real avg_rtt
            avg_rtt = 1000
            sla_max_rtt = int(self.scenario_cfg["sla"]["max_rtt"])
            assert avg_rtt <= sla_max_rtt, "avg_rtt %d > sla_max_rtt %d; " \
                % (avg_rtt, sla_max_rtt)


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {
        'host': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename
        },
        'target': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename,
            'ipaddr': '10.229.47.137',
        }
    }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    options = {'packetsize': 120}
    args = {'options': options}
    result = {}

    p = PktgenDPDKLatency(args, ctx)
    p.run(result)
    print result

if __name__ == '__main__':
    _test()
