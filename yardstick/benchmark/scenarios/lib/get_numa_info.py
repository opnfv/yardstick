# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging

from xml.etree import ElementTree as ET

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class GetNumaInfo(base.ClientServerScenario):
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "GetNumaInfo"
    LOGGER = LOG

    def __init__(self, scenario_cfg, context_cfg):
        super(GetNumaInfo, self).__init__(scenario_cfg, context_cfg)
        self.node_key = self.server_id = self.options['server']['id']

    def _run(self, result):
        return [self._check_numa_node()]

    def _check_numa_node(self):
        cmd = "sudo virsh dumpxml %s" % self.server_id
        LOG.debug("Executing command: %s", cmd)
        stdout = self._exec_cmd_with_raise(self.host_client, cmd)

        root = ET.fromstring(stdout)
        return {
            "pinning": [a.attrib for a in root.iter('vcpupin')],
            'vcpupin': [a.attrib for a in root.iter('memnode')],
        }
