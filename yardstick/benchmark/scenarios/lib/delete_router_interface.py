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


class DeleteRouterInterface(base.Scenario):
    """Unset an OpenStack router interface"""

    __scenario_type__ = "DeleteRouterInterface"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.subnet_id = self.options.get("subnet_id", None)
        self.router_id = self.options.get("router_id", None)

        self.neutron_client = op_utils.get_neutron_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = op_utils.remove_interface_router(self.neutron_client,
                                                  router_id=self.router_id,
                                                  subnet_id=self.subnet_id)
        if status:
            result.update({"delete_router_interface": 1})
            LOG.info("Delete router interface successful!")
        else:
            result.update({"delete_router_interface": 0})
            LOG.error("Delete router interface failed!")
