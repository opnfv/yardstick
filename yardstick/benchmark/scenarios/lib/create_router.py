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

        self.name = self.options.get('name', None)
        self.admin_state_up = self.options.get('admin_state_up', True)
        self.ext_gateway_net_id = self.options.get('ext_gateway_net_id', None)
        self.enable_snat = self.options.get('enable_snat', None)
        self.ext_fixed_ips = self.options.get('ext_fixed_ips', None)
        self.project_id = self.options.get('project_id', None)
        self.availability_zone_hints = self.options.get(
            'availability_zone_hints', None)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, *args):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        router_id = openstack_utils.create_neutron_router(
            self.shade_client, self.name, self.admin_state_up,
            self.ext_gateway_net_id, self.enable_snat, self.ext_fixed_ips,
            self.project_id, self.availability_zone_hints)
        if not router_id:
            LOG.error("Create router failed!")
            return

        LOG.info("Create router successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [router_id]
        return self._push_to_outputs(keys, values)
