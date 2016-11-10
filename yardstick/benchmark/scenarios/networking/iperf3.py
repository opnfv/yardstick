##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# iperf3 scenario
# iperf3 homepage at: http://software.es.net/iperf/

import logging
import json
import pkg_resources

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Iperf(base.Scenario):
    """Execute iperf3 between two hosts

By default TCP is used but UDP can also be configured.
For more info see http://software.es.net/iperf

  Parameters
    bytes - number of bytes to transmit
      only valid with a non duration runner, mutually exclusive with blockcount
        type:    int
        unit:    bytes
        default: 56
    udp - use UDP rather than TCP
        type:    bool
        unit:    na
        default: false
    nodelay - set TCP no delay, disabling Nagle's Algorithm
        type:    bool
        unit:    na
        default: false
    blockcount - number of blocks (packets) to transmit,
      only valid with a non duration runner, mutually exclusive with bytes
        type:    int
        unit:    bytes
        default: -
    """
    __scenario_type__ = "Iperf3"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
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
        self.target = ssh.SSH(target_user, target_ip,
                              key_filename=target_key_filename,
                              port=target_ssh_port)
        self.target.wait(timeout=600)

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.host = ssh.SSH(host_user, host_ip,
                            key_filename=host_key_filename, port=host_ssh_port)
        self.host.wait(timeout=600)

        cmd = "iperf3 -s -D"
        LOG.debug("Starting iperf3 server with command: %s", cmd)
        status, _, stderr = self.target.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        self.setup_done = True

    def teardown(self):
        LOG.debug("teardown")
        self.host.close()
        status, stdout, stderr = self.target.execute("pkill iperf3")
        if status:
            LOG.warn(stderr)
        self.target.close()

    def run(self, result):
        """execute the benchmark"""
        if not self.setup_done:
            self.setup()

        # if run by a duration runner, get the duration time and setup as arg
        time = self.scenario_cfg["runner"].get("duration", None) \
            if "runner" in self.scenario_cfg else None
        options = self.scenario_cfg['options']

        cmd = "iperf3 -c %s --json" % (self.context_cfg['target']['ipaddr'])

        # If there are no options specified
        if not options:
            options = ""

        use_UDP = False
        if "udp" in options:
            cmd += " --udp"
            use_UDP = True
            if "bandwidth" in options:
                cmd += " --bandwidth %s" % options["bandwidth"]
        else:
            # tcp obviously
            if "nodelay" in options:
                cmd += " --nodelay"

        # these options are mutually exclusive in iperf3
        if time:
            cmd += " %d" % time
        elif "bytes" in options:
            # number of bytes to transmit (instead of --time)
            cmd += " --bytes %d" % options["bytes"]
        elif "blockcount" in options:
            cmd += " --blockcount %d" % options["blockcount"]

        LOG.debug("Executing command: %s", cmd)

        status, stdout, stderr = self.host.execute(cmd)
        if status:
            # error cause in json dict on stdout
            raise RuntimeError(stdout)

        # Note: convert all ints to floats in order to avoid
        # schema conflicts in influxdb. We probably should add
        # a format func in the future.
        result.update(json.loads(stdout, parse_int=float))

        if "sla" in self.scenario_cfg:
            sla_iperf = self.scenario_cfg["sla"]
            if not use_UDP:
                sla_bytes_per_second = int(sla_iperf["bytes_per_second"])

                # convert bits per second to bytes per second
                bit_per_second = \
                    int(result["end"]["sum_received"]["bits_per_second"])
                bytes_per_second = bit_per_second / 8
                assert bytes_per_second >= sla_bytes_per_second, \
                    "bytes_per_second %d < sla:bytes_per_second (%d); " % \
                    (bytes_per_second, sla_bytes_per_second)
            else:
                sla_jitter = float(sla_iperf["jitter"])

                jitter_ms = float(result["end"]["sum"]["jitter_ms"])
                assert jitter_ms <= sla_jitter, \
                    "jitter_ms  %f > sla:jitter %f; " % \
                    (jitter_ms, sla_jitter)


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

    p = Iperf(args, ctx)
    p.run(result)
    print result

if __name__ == '__main__':
    _test()
