##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import pkg_resources
import logging

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Ping_node(base.Scenario):
    """Execute ping between two nodes

  Parameters
    packetsize - number of data bytes to send
        type:    int
        unit:    bytes
        default: 56
    """

    __scenario_type__ = "Ping_node"

    TARGET_SCRIPT = 'ping_benchmark.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping_node.TARGET_SCRIPT)

        options = self.scenario_cfg['options']
        host_node_name = options.get('host', 'node1')
        target_node_name = options.get('target', 'node2')

        nodes = self.context_cfg['nodes']
        self.host_node = nodes.get(host_node_name, None)
        self.target_node = nodes.get(target_node_name, None)

        host_user = self.host_node.get('user', 'ubuntu')
        host_ip = self.host_node.get('ip', None)
        key_filename = self.host_node.get('key_filename', '~/.ssh/id_rsa')

        LOG.debug("user:%s, host:%s", host_user, host_ip)
        self.connection = ssh.SSH(host_user, host_ip,
                                  key_filename=key_filename)
        self.connection.wait()

    def run(self, result):
        """execute the benchmark"""

        if "options" in self.scenario_cfg:
            options = "-s %s" % \
                self.scenario_cfg['options'].get("packetsize", '56')
        else:
            options = ""

        destination = self.target_node.get("ip", '127.0.0.1')

        LOG.debug("ping '%s' '%s'", options, destination)

        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} {1}".format(destination, options),
            stdin=open(self.target_script, "r"))

        if exit_status != 0:
            raise RuntimeError(stderr)

        if stdout:
            result["rtt"] = float(stdout)

            if "sla" in self.scenario_cfg:
                sla_max_rtt = int(self.scenario_cfg["sla"]["max_rtt"])
                assert result["rtt"] <= sla_max_rtt, \
                    "rtt %f > sla:max_rtt(%f); " % (result["rtt"], sla_max_rtt)
        else:
            LOG.error("ping '%s' '%s' timeout", options, destination)
