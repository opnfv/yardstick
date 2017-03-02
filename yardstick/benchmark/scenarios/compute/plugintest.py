##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import logging

from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class PluginTest(base.Scenario):
    """Sample scenario file for testing sample plugin"""
    __scenario_type__ = "PluginTest"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""

        nodes = self.context_cfg['nodes']
        node = nodes.get('host1', None)

        self.client = ssh.SSH.from_node(node, defaults={
            "user": "ubuntu", "password": "root"
        })
        self.client.wait(timeout=600)

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        cmd = "sudo bash test.sh"

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))
