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
    """Execute ping between two hosts

  Parameters
    packetsize - number of data bytes to send
        type:    int
        unit:    bytes
        default: 56
    """

    __scenario_type__ = "Ping"

    TARGET_SCRIPT = 'ping_benchmark.bash'

    def __init__(self, context):
        self.context = context
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking', Ping.TARGET_SCRIPT)
        host = self.context['host']
        user = host.get('user', 'ubuntu')
        ip = host.get('ip', None)
        key_filename = host.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, host:%s", user, ip)

        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait()

    def run(self, args, result):
        """execute the benchmark"""

        if "options" in args:
            options = "-s %s" % args['options'].get("packetsize", '56')
        else:
            options = ""

        destination = self.context['target'].get("ipaddr", '127.0.0.1')

        LOG.debug("ping '%s' '%s'", options, destination)

        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} {1}".format(destination, options),
            stdin=open(self.target_script, "r"))

        if exit_status != 0:
            raise RuntimeError(stderr)

        result["rtt"] = float(stdout)

        if "sla" in args:
            sla_max_rtt = int(args["sla"]["max_rtt"])
            assert result["rtt"] <= sla_max_rtt, "rtt %f > sla:max_rtt(%f); " % \
                (result["rtt"], sla_max_rtt)


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename("yardstick.resources",
                                                   "files/yardstick_key")
    ctx = {
        "host": {
            "ip": "10.229.47.137",
            "user": "root",
            "key_filename": key_filename
        },
        "target": {
            "ipaddr": "10.229.17.105",
        }
    }

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    p = Ping(ctx)
    args = {}
    result = {}

    p.run(args, result)
    print result

if __name__ == '__main__':
    _test()
