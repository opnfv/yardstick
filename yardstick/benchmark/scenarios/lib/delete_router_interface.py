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


class DeleteRouterInterface(base.Scenario):
    """Unset an OpenStack router interface"""

    __scenario_type__ = "DeleteRouterInterface"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.router = self.options.get("router", None)
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

        status = openstack_utils.remove_router_interface(
            self.shade_client, self.router, self.subnet_id, self.port_id)
        if status:
            result.update({"delete_router_interface": 1})
            LOG.info("Delete router interface successful!")
        else:
            result.update({"delete_router_interface": 0})
            LOG.error("Delete router interface failed!")
        return status
