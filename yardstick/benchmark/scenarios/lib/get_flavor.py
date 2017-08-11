##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging

from yardstick.benchmark.scenarios import base
import yardstick.common.openstack_utils as op_utils

LOG = logging.getLogger(__name__)


class GetFlavor(base.Scenario):
    """Get an OpenStack flavor by name"""

    __scenario_type__ = "GetFlavor"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']
        self.flavor_name = self.options.get("flavor_name", "TestFlavor")
        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        LOG.info("Querying flavor: %s", self.flavor_name)
        flavor = op_utils.get_flavor_by_name(self.flavor_name)
        if flavor:
            LOG.info("Get flavor successful!")
            values = [self._change_obj_to_dict(flavor)]
        else:
            LOG.info("Get flavor: no flavor matched!")
            values = []

        keys = self.scenario_cfg.get('output', '').split()
        return self._push_to_outputs(keys, values)
