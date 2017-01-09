##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# ping scenario

from __future__ import print_function
from __future__ import absolute_import
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

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking', Ping.TARGET_SCRIPT)
        host = self.context_cfg['host']
        user = host.get('user', 'ubuntu')
        ssh_port = host.get("ssh_port", ssh.DEFAULT_PORT)
        ip = host.get('ip', None)
        key_filename = host.get('key_filename', '/root/.ssh/id_rsa')
        password = host.get('password', None)

        if password is not None:
            LOG.info("Log in via pw, user:%s, host:%s, pw:%s",
                     user, ip, password)
            self.connection = ssh.SSH(user, ip, password=password,
                                      port=ssh_port)
        else:
            LOG.info("Log in via key, user:%s, host:%s, key_filename:%s",
                     user, ip, key_filename)
            self.connection = ssh.SSH(user, ip, key_filename=key_filename,
                                      port=ssh_port)

        self.connection.wait(timeout=600)

    def run(self, result):
        """execute the benchmark"""

        if "options" in self.scenario_cfg:
            options = "-s %s" % \
                self.scenario_cfg['options'].get("packetsize", '56')
        else:
            options = ""

        destination = self.context_cfg['target'].get('ipaddr', '127.0.0.1')
        dest_list = [s.strip() for s in destination.split(',')]

        result["rtt"] = {}
        rtt_result = result["rtt"]

        for pos, dest in enumerate(dest_list):
            if 'targets' in self.scenario_cfg:
                target_vm = self.scenario_cfg['targets'][pos]
            else:
                target_vm = self.scenario_cfg['target']

            LOG.debug("ping '%s' '%s'", options, dest)
            with open(self.target_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "/bin/sh -s {0} {1}".format(dest, options),
                    stdin=stdin_file)

            if exit_status != 0:
                raise RuntimeError(stderr)

            if stdout:
                target_vm_name = target_vm.split('.')[0]
                rtt_result[target_vm_name] = float(stdout)
                if "sla" in self.scenario_cfg:
                    sla_max_rtt = int(self.scenario_cfg["sla"]["max_rtt"])
                    assert rtt_result[target_vm_name] <= sla_max_rtt,\
                        "rtt %f > sla: max_rtt(%f); " % \
                        (rtt_result[target_vm_name], sla_max_rtt)
            else:
                LOG.error("ping '%s' '%s' timeout", options, target_vm)


def _test():    # pragma: no cover
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

    args = {}
    result = {}

    p = Ping(args, ctx)
    p.run(result)
    print(result)


if __name__ == '__main__':    # pragma: no cover
    _test()
