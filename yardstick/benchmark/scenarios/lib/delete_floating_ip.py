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


class DeleteFloatingIp(base.Scenario):
    """Delete an OpenStack floating ip """

    __scenario_type__ = "DeleteFloatingIp"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.floating_ip_id = self.options.get("floating_ip_id", None)

        self.nova_client = op_utils.get_nova_client()
        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = op_utils.delete_floating_ip(nova_client=self.nova_client,
                                             floatingip_id=self.floating_ip_id)
        if status:
            result.update({"delete_floating_ip": 1})
            LOG.info("Delete floating ip successful!")
        else:
            result.update({"delete_floating_ip": 0})
            LOG.error("Delete floating ip failed!")
