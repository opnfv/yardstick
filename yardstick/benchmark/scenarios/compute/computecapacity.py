##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
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


class ComputeCapacity(base.Scenario):
    """Measure compute capacity and scale.

    This scenario reads hardware specification, including number of cpus,
    number of cores, number of threads, available memory size and total cache
    size of a host.
    """
    __scenario_type__ = "ComputeCapacity"
    TARGET_SCRIPT = "computecapacity.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            ComputeCapacity.TARGET_SCRIPT)

        nodes = self.context_cfg['nodes']
        node = nodes.get('host1', None)
        host_user = node.get('user', 'ubuntu')
        host_ip = node.get('ip', None)
        host_pwd = node.get('password', 'root')
        LOG.debug("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip, password=host_pwd)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/computecapacity.sh",
                        stdin=open(self.target_script, 'rb'))

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        cmd = "sudo bash computecapacity.sh"

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))
