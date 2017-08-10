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


class CreateFlavor(base.Scenario):
    """Create an OpenStack flavor"""

    __scenario_type__ = "CreateFlavor"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.flavor_name = self.options.get("flavor_name", "TestFlavor")
        self.vcpus = self.options.get("vcpus", 2)
        self.ram = self.options.get("ram", 1024)
        self.disk = self.options.get("disk", 100)
        self.public = self.options.get("is_public", True)

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        LOG.info("Creating flavor %s with %s vcpus, %sMB ram and %sGB disk",
                 self.flavor_name, self.vcpus, self.ram, self.disk)
        paras = {'is_public': self.public}
        flavor = op_utils.create_flavor(self.flavor_name,
                                        self.ram, self.vcpus, self.disk,
                                        **paras)

        if flavor:
            LOG.info("Create flavor successful!")
            values = [flavor.id]
        else:
            LOG.info("Create flavor failed!")
            values = []

        keys = self.scenario_cfg.get('output', '').split()
        return self._push_to_outputs(keys, values)
