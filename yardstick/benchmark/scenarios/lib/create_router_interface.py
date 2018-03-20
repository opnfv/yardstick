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
from yardstick.common import exceptions
from yardstick.common import openstack_utils

LOG = logging.getLogger(__name__)


class CreateRouterInterface(base.Scenario):
    """Set an OpenStack router interface"""

    __scenario_type__ = "CreateRouterInterface"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.router_id = self.options["router_id"]
        self.subnet_id = self.options.get("subnet_id", None)
        self.port_id = self.options.get("port_id", None)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        router = self.shade_client.get_router(self.router_id)

        interface_id = openstack_utils.create_router_interface(
            self.shade_client, router, subnet_id=self.subnet_id,
            port_id=self.port_id)

        if not interface_id:
            result.update({"create_router_interface": 0})
            LOG.error("Create router interface failed!")
            raise exceptions.ScenarioCreateRouterIntError

        result.update({"create_router_interface": 1})
        LOG.info("Create router interface successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [interface_id]
        return self._push_to_outputs(keys, values)
