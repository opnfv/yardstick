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
        user = self.context.get('user', 'ubuntu')
        host = self.context.get('host', None)
        key_filename = self.context.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, host:%s", user, host)

        self.connection = ssh.SSH(user, host, key_filename=key_filename)
        self.connection.wait()

    def run(self, args):
        """execute the benchmark"""

        if "options" in args:
            options = "-s %s" % args['options'].get("packetsize", '56')
        else:
            options = ""

        destination = args.get("ipaddr", '127.0.0.1')

        LOG.debug("ping '%s' '%s'", options, destination)

        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} {1}".format(destination, options),
            stdin=open(self.target_script, "r"))

        if exit_status != 0:
            raise RuntimeError(stderr)

        if stdout:
            rtt = float(stdout)
            if "sla" in args:
                sla_max_rtt = int(args["sla"]["max_rtt"])
                assert rtt <= sla_max_rtt, "rtt %f > sla:max_rtt(%f)" % \
                    (rtt, sla_max_rtt)

            return rtt
        else:
            LOG.error("ping '%s' '%s' timeout", options, destination)
