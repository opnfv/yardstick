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


class DeleteFlavor(base.Scenario):
    """Delete an OpenStack flavor by name or id

    Parameters
        flavor_name - name of the flavor
            type:    string
            unit:    N/A
            default: null
        flavor_id - id of the flavor
            type:    string
            unit:    N/A
            default: null
    """

    __scenario_type__ = "DeleteFlavor"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.flavor_name = self.options.get("flavor_name", None)
        self.flavor_id = self.options.get("flavor_id", None)

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        if self.flavor_name and not self.flavor_id:
            self.flavor_id = op_utils.get_flavor_id(self.flavor_name)
        
        LOG.info("Deleting flavor: %s", self.flavor_id)
        status = op_utils.delete_flavor(self.flavor_id)

        if status:
            LOG.info("Delete flavor successful!")
        else:
            LOG.info("Delete flavor failed!")
