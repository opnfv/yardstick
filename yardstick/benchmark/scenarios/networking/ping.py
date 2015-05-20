##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# ping scenario

import pkg_resources
import logging

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Ping(base.Scenario):
    """Executes a ping benchmark between two hosts"""
    __scenario_type__ = "Ping"

    TARGET_SCRIPT = 'ping_benchmark.bash'

    def __init__(self, context):
        self.context = context
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking', Ping.TARGET_SCRIPT)
        user = self.context.get('user', 'ubuntu')
        host = self.context.get('host', None)
        key_filename = self.context.get('key_filename', '~/.ssh/id_rsa')

        LOG.debug("user:%s, host:%s", user, host)

        self.connection = ssh.SSH(user, host, key_filename=key_filename)
        self.connection.wait()

    def run(self, args):
        """execute the benchmark"""

        self.options = "-s %s" % args['options'].get("packetsize", '56')
        self.ipaddr = args.get("ipaddr", '127.0.0.1')

        LOG.debug("ping %s %s", self.options, self.ipaddr)

        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} {1}".format(self.ipaddr, self.options),
            stdin=open(self.target_script, "r"))

        if exit_status != 0:
            raise RuntimeError(stderr)

        rtt = float(stdout)

        if "sla" in args:
            sla_max_rtt = int(args["sla"]["max_rtt"])
            assert rtt <= sla_max_rtt, "rtt %f > sla_max_rtt" % rtt

        return rtt


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {'host': '172.16.0.137',
           'user': 'cirros',
           'key_filename': key_filename}
    p = Ping(ctx)
    args = {'options': '-c 2 -s 200',
            'ipaddr': '172.16.0.138'}
    result = p.run(args)
    print result

if __name__ == '__main__':
    _test()
