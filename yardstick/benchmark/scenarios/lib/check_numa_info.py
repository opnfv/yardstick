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


class CheckNumaInfo(base.Scenario):
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "CheckNumaInfo"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        self.options = self.scenario_cfg.get('options', {})

        self.cpu_set = self.options.get('cpu_set', '1,2,3,4,5,6')

    def run(self, result):
        info1 = self.options.get('info1')
        info2 = self.options.get('info2')
        LOG.debug('Origin numa info: %s', info1)
        LOG.debug('Current numa info: %s', info2)
        status = self._check_vm2_status(info1, info2)

        keys = self.scenario_cfg.get('output', '').split()
        values = [status]
        return self._push_to_outputs(keys, values)

    def _check_vm2_status(self, info1, info2):
        if len(info1['pinning']) != 1 or len(info2['pinning']) != 1:
            return False

        for i in info1['vcpupin']:
            for j in i['cpuset'].split(','):
                if j not in self.cpu_set.split(','):
                    return False

        for i in info2['vcpupin']:
            for j in i['cpuset'].split(','):
                if j not in self.cpu_set.split(','):
                    return False

        return True
