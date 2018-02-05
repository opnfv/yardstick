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


class CreateNetwork(base.Scenario):
    """Create an OpenStack network"""

    __scenario_type__ = "CreateNetwork"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.network_name = self.options.get("network_name", None)
        self.shared = self.options.get("shared", False)
        self.admin_state = self.options.get("admin_state", True)
        self.external = self.options.get("external", False)
        self.provider = self.options.get("provider", None)
        self.project_id = self.options.get("project_id", None)
        self.availability_zone_hints = self.options.get(
            "availability_zone_hints", None)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, *args):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        network_id = openstack_utils.create_neutron_net(
            self.shade_client, self.network_name, self.shared,
            self.admin_state, self.external, self.provider, self.project_id,
            self.availability_zone_hints)
        if not network_id:
            LOG.error("Create network failed!")
            return

        LOG.info("Create network successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [network_id]
        return self._push_to_outputs(keys, values)
