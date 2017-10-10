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

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class AddMemoryLoad(base.ClientServerScenario):
    """Add memory load in server
    """

    __scenario_type__ = "AddMemoryLoad"
    LOGGER = LOG

    def __init__(self, scenario_cfg, context_cfg):
        super(AddMemoryLoad, self).__init__(scenario_cfg, context_cfg)
        self.node_key = self.server_name

    def _run(self, result):
        self._add_load()

    def _add_load(self):
        try:
            memory_load = float(self.options['memory_load'])
        except KeyError:
            LOG.error('memory_load parameter must be provided as a number')
            return

        if not memory_load:
            return

        cmd = 'free'
        code, stdout, stderr = self.host_client.execute(cmd)
        mem_info = next(line for line in stdout.splitlines() if line.startswith('Mem:')).split()
        total_mem = int(mem_info[1])
        used_mem = int(mem_info[2])
        vm_load = (total_mem * memory_load - used_mem) / 1024 / 128
        if vm_load <= 0:
            return

        LOG.info('Add %s vm load', vm_load)
        cmd = 'stress -t 10 -m {} --vm-keep'.format(vm_load)
        self.host_client.execute(cmd)
