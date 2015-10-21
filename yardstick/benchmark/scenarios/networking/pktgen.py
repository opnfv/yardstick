##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import logging
import json

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Pktgen(base.Scenario):
    """Execute pktgen between two hosts

  Parameters
    packetsize - packet size in bytes without the CRC
        type:    int
        unit:    bytes
        default: 60
    number_of_ports - number of UDP ports to test
        type:    int
        unit:    na
        default: 10
    duration - duration of the test
        type:    int
        unit:    seconds
        default: 20
    """
    __scenario_type__ = "Pktgen"

    TARGET_SCRIPT = 'pktgen_benchmark.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Pktgen.TARGET_SCRIPT)
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

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip,
                              key_filename=host_key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/pktgen.sh",
                        stdin=open(self.target_script, "rb"))

        self.setup_done = True

    def _iptables_setup(self):
        """Setup iptables on server to monitor for received packets"""
        cmd = "sudo iptables -F; " \
              "sudo iptables -A INPUT -p udp --dport 1000:%s -j DROP" \
              % (1000 + self.number_of_ports)
        LOG.debug("Executing command: %s", cmd)
        status, _, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)

    def _iptables_get_result(self):
        """Get packet statistics from server"""
        cmd = "sudo iptables -L INPUT -vnx |" \
              "awk '/dpts:1000:%s/ {{printf \"%%s\", $1}}'" \
              % (1000 + self.number_of_ports)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.server.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        return int(stdout)

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        ipaddr = self.context_cfg["target"].get("ipaddr", '127.0.0.1')

        options = self.scenario_cfg['options']
        packetsize = options.get("packetsize", 60)
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

        self._iptables_setup()

        cmd = "sudo bash pktgen.sh %s %s %s %s" \
            % (ipaddr, self.number_of_ports, packetsize, duration)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))

        result['packets_received'] = self._iptables_get_result()

        if "sla" in self.scenario_cfg:
            sent = result['packets_sent']
            received = result['packets_received']
            ppm = 1000000 * (sent - received) / sent
            sla_max_ppm = int(self.scenario_cfg["sla"]["max_ppm"])
            assert ppm <= sla_max_ppm, "ppm %d > sla_max_ppm %d; " \
                % (ppm, sla_max_ppm)


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

    p = Pktgen(args, ctx)
    p.run(result)
    print result

if __name__ == '__main__':
    _test()
