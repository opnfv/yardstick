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
from yardstick.common import exceptions

LOG = logging.getLogger(__name__)


class CreateRouter(base.Scenario):
    """Create an OpenStack router"""

    __scenario_type__ = "CreateRouter"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.name = self.options.get('name')
        self.admin_state_up = self.options.get('admin_state_up', True)
        self.ext_gateway_net_id = self.options.get('ext_gateway_net_id')
        self.enable_snat = self.options.get('enable_snat')
        self.ext_fixed_ips = self.options.get('ext_fixed_ips')
        self.project_id = self.options.get('project_id')

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        router_id = openstack_utils.create_neutron_router(
            self.shade_client, name=self.name, admin_state_up=
            self.admin_state_up, ext_gateway_net_id=self.ext_gateway_net_id,
            enable_snat=self.enable_snat, ext_fixed_ips=self.ext_fixed_ips,
            project_id=self.project_id)
        if not router_id:
            result.update({"router_create": 0})
            LOG.error("Create router failed!")
            raise exceptions.ScenarioCreateRouterError

        result.update({"router_create": 1})
        LOG.info("Create router successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [router_id]
        return self._push_to_outputs(keys, values)
