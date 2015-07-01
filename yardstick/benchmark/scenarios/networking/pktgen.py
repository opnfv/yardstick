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
LOG.setLevel(logging.DEBUG)


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

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Pktgen.TARGET_SCRIPT)
        user = self.context.get('user', 'ubuntu')
        host = self.context.get('host', None)
        target = self.context.get('target', None)
        key_filename = self.context.get('key_filename', '~/.ssh/id_rsa')

        LOG.debug("user:%s, target:%s", user, target)
        self.server = ssh.SSH(user, target, key_filename=key_filename)
        self.server.wait(timeout=600)

        LOG.debug("user:%s, host:%s", user, host)
        self.client = ssh.SSH(user, host, key_filename=key_filename)
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

    def _iptables_clear_counters(self):
        """Zero iptables packet and byte counters"""
        cmd = "sudo iptables -Z;"
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

    def run(self, args):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        ipaddr = args.get("ipaddr", '127.0.0.1')

        options = args['options']
        packetsizes = options.get("packetsize", 60)

        # If there is only one packet size specified in a non-list format
        if isinstance(packetsizes, int):
            packetsizes = [packetsizes]

        self.number_of_ports = options.get("number_of_ports", 10)
        # if run by a duration runner
        duration_time = self.context.get("duration", None)
        # if run by an arithmetic runner
        arithmetic_time = options.get("duration", None)

        if duration_time:
            duration = duration_time
        elif arithmetic_time:
            duration = arithmetic_time
        else:
            duration = 20

        self._iptables_setup()

        results = []
        for packetsize in packetsizes:
            self._iptables_clear_counters()

            cmd = "sudo bash pktgen.sh %s %s %s %s" \
                % (ipaddr, self.number_of_ports, packetsize, duration)
            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)

            if status:
                raise RuntimeError(stderr)

            data = json.loads(stdout)
            data['packets_received'] = self._iptables_get_result()

            if "sla" in args:
                sent = data['packets_sent']
                received = data['packets_received']
                ppm = 1000000 * (sent - received) / sent
                sla_max_ppm = int(args["sla"]["max_ppm"])
                assert ppm <= sla_max_ppm, "ppm %d > sla_max_ppm %d" \
                    % (ppm, sla_max_ppm)

            results.append(data)

        # No need for a list output if there is a single resultset
        if len(results) == 1:
            results = results[0]
        return results


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {'host': '172.16.0.137',
           'target': '172.16.0.138',
           'user': 'ubuntu',
           'key_filename': key_filename
           }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    p = Pktgen(ctx)

    options = {'packetsize': 120}

    args = {'options': options,
            'ipaddr': '192.168.111.31'}
    result = p.run(args)
    print result

if __name__ == '__main__':
    _test()
