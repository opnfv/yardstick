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


class Ping6(base.Scenario):  # pragma: no cover
    """Execute ping6 between two hosts

    read link below for more ipv6 info description:
    http://wiki.opnfv.org/ipv6_opnfv_project
    """
    __scenario_type__ = "Ping6"

    TARGET_SCRIPT = 'ping6_benchmark.bash'
    SETUP_SCRIPT = 'ping6_setup.bash'
    TEARDOWN_SCRIPT = 'ping6_teardown.bash'
    METADATA_SCRIPT = 'ping6_metadata.txt'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.run_done = False

    def _ssh_host(self):
        # ssh host1
        host = self.context_cfg['host']
        host_user = host.get('user', 'ubuntu')
        host_ip = host.get('ip', None)
        host_pwd = host.get('password', 'root')
        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip, password=host_pwd)
        self.client.wait(timeout=600)

    def setup(self):
        '''scenario setup'''
        self.setup_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.SETUP_SCRIPT)

        self.ping6_metadata_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.METADATA_SCRIPT)
        # ssh host1
        self._ssh_host()
        # run script to setup ipv6
        self.client.run("cat > ~/setup.sh",
                        stdin=open(self.setup_script, "rb"))
        self.client.run("cat > ~/metadata.txt",
                        stdin=open(self.ping6_metadata_script, "rb"))
        cmd = "sudo bash setup.sh"
        status, stdout, stderr = self.client.execute(cmd)

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        # ssh vm1
        self.ping6_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.TARGET_SCRIPT)

        if not self.setup_done:
            self._ssh_host()

        self.client.run("cat > ~/ping6.sh",
                        stdin=open(self.ping6_script, "rb"))
        cmd = "sudo bash ping6.sh"
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        print stdout
        if status:
            raise RuntimeError(stderr)

        if stdout:
            result["rtt"] = float(stdout)

            if "sla" in self.scenario_cfg:
                sla_max_rtt = int(self.scenario_cfg["sla"]["max_rtt"])
                assert result["rtt"] <= sla_max_rtt, "rtt %f > sla:max_rtt(%f); " % \
                    (result["rtt"], sla_max_rtt)
        else:
            LOG.error("ping6 timeout")
        self.run_done = True

    def teardown(self):
        """teardown the benchmark"""

        if not self.run_done:
            self._ssh_host()

        self.teardown_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ping6.TEARDOWN_SCRIPT)
        self.client.run("cat > ~/teardown.sh",
                        stdin=open(self.teardown_script, "rb"))
        cmd = "sudo bash teardown.sh"
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        if stdout:
            pass
        else:
            LOG.error("ping6 teardown failed")
