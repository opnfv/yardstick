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


class CreateNetwork(base.Scenario):
    """Create an OpenStack network"""

    __scenario_type__ = "CreateNetwork"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.network_name = self.options.get("network_name", None)

        self.shade_client = op_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        network_id = op_utils.create_neutron_net(self.shade_client,
                                                 network_name=self.network_name)
        if not network_id:
            result.update({"network_create": 0})
            LOG.error("Create network failed!")
            return

        result.update({"network_create": 1})
        LOG.info("Create network successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [network_id]
        return self._push_to_outputs(keys, values)
