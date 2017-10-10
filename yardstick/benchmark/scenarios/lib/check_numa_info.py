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
from itertools import chain

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CheckNumaInfo(base.Scenario):
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "CheckNumaInfo"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        'cpu_set': '1,2,3,4,5,6',
    }

    def _run(self, result):
        return [self._check_vm2_status()]

    def _check_vm2_status(self):
        LOG.debug('Origin numa info: %s', self.info1)
        LOG.debug('Current numa info: %s', self.info2)
        if len(self.info1['pinning']) != 1 or len(self.info2['pinning']) != 1:
            return False

        cpu_set = set(self.cpu_set.split(','))
        pin_iter = chain(self.info1['vcpupin'], self.info2['vcpupin'])
        pin_set_iter = (set(pin['cpuset'].split(',')) for pin in pin_iter)
        return not any(pin_set.difference(cpu_set) for pin_set in pin_set_iter)
