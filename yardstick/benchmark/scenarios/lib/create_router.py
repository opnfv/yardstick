##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging

from yardstick.benchmark.scenarios import base
from yardstick.common import openstack_utils

LOG = logging.getLogger(__name__)


class CreateRouter(base.Scenario):
    """Create an OpenStack router"""

    __scenario_type__ = "CreateRouter"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

      #  self.openstack = self.options.get("openstack_paras", None)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, *args):
        """execute the test"""

        if not self.setup_done:
            self.setup()

       # openstack_paras = {'router': self.openstack}
        router_id = openstack_utils.create_neutron_router(self.shade_client)
        if not router_id:
            LOG.error("Create router failed!")
            return

        LOG.info("Create router successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [router_id]
        return self._push_to_outputs(keys, values)
