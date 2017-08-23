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


class DeleteVolume(base.Scenario):
    """Delete an OpenStack volume"""

    __scenario_type__ = "DeleteVolume"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.volume_id = self.options.get("volume_id", None)

        self.cinder_client = op_utils.get_cinder_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = op_utils.delete_volume(self.cinder_client, self.volume_id)

        if status:
            result.update({"delete_volume": 1})
            LOG.info("Delete volume successful!")
        else:
            result.update({"delete_volume": 0})
            LOG.info("Delete volume failed!")
