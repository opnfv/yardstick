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
LOG.setLevel(logging.DEBUG)


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

    def __init__(self, context):
        self.context = context
        self.user = context.get('user', 'ubuntu')
        self.host_ipaddr = context['host']
        self.target_ipaddr = context['target_ipaddr']
        self.key_filename = self.context.get('key_filename', '~/.ssh/id_rsa')
        self.setup_done = False

    def setup(self):
        LOG.debug("setup, key %s", self.key_filename)
        LOG.debug("host:%s, user:%s", self.host_ipaddr, self.user)
        self.host = ssh.SSH(self.user, self.host_ipaddr,
                            key_filename=self.key_filename)
        self.host.wait(timeout=600)

        LOG.debug("target:%s, user:%s", self.target_ipaddr, self.user)
        self.target = ssh.SSH(self.user, self.target_ipaddr,
                              key_filename=self.key_filename)
        self.target.wait(timeout=600)

        cmd = "iperf3 -s -D"
        LOG.debug("Starting iperf3 server with command: %s", cmd)
        status, _, stderr = self.target.execute(cmd)
        if status:
            raise RuntimeError(stderr)

    def teardown(self):
        LOG.debug("teardown")
        self.host.close()
        status, stdout, stderr = self.target.execute("pkill iperf3")
        if status:
            LOG.warn(stderr)
        self.target.close()

    def run(self, args):
        """execute the benchmark"""

        # if run by a duration runner, get the duration time and setup as arg
        time = self.context.get('duration', None)
        options = args['options']

        cmd = "iperf3 -c %s --json" % (self.target_ipaddr)

        if "udp" in options:
            cmd += " --udp"
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

        output = json.loads(stdout)

        # convert bits per second to bytes per second
        bytes_per_second = \
            int((output["end"]["sum_received"]["bits_per_second"])) / 8

        if "sla" in args:
            sla_bytes_per_second = int(args["sla"]["bytes_per_second"])
            assert bytes_per_second >= sla_bytes_per_second, \
                "bytes_per_second %d < sla (%d)" % \
                (bytes_per_second, sla_bytes_per_second)

        return output


def _test():
    '''internal test function'''

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    runner_cfg = {}
    runner_cfg['type'] = 'Duration'
    runner_cfg['duration'] = 5
    runner_cfg['host'] = '10.0.2.33'
    runner_cfg['target_ipaddr'] = '10.0.2.53'
    runner_cfg['user'] = 'ubuntu'
    runner_cfg['output_filename'] = "/tmp/yardstick.out"
    runner_cfg['key_filename'] = key_filename

    scenario_args = {}
    scenario_args['options'] = {"bytes": 10000000000}
    scenario_args['sla'] = \
        {"bytes_per_second": 2900000000, "action": "monitor"}

    from yardstick.benchmark.runners import base as base_runner
    runner = base_runner.Runner.get(runner_cfg)
    runner.run("Iperf3", scenario_args)
    runner.join()
    base_runner.Runner.release(runner)

if __name__ == '__main__':
    _test()
