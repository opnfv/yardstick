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

import time
import logging

from yardstick.benchmark.scenarios import base
import yardstick.common.openstack_utils as op_utils

LOG = logging.getLogger(__name__)


class CreateVolume(base.Scenario):
    """Create an OpenStack volume"""

    __scenario_type__ = "CreateVolume"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.volume_name = self.options.get("volume_name", "TestVolume")
        self.volume_size = self.options.get("size", 100)
        self.image_name = self.options.get("image", None)
        self.image_id = None

        self.glance_client = op_utils.get_glance_client()
        self.cinder_client = op_utils.get_cinder_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        if self.image_name:
            self.image_id = op_utils.get_image_id(self.glance_client,
                                                  self.image_name)

        volume = op_utils.create_volume(self.cinder_client, self.volume_name,
                                        self.volume_size, self.image_id)

        status = volume.status
        while(status == 'creating' or status == 'downloading'):
            LOG.info("Volume status is: %s" % status)
            time.sleep(5)
            volume = op_utils.get_volume_by_name(self.volume_name)
            status = volume.status

        LOG.info("Create volume successful!")

        values = [volume.id]
        keys = self.scenario_cfg.get('output', '').split()
        return self._push_to_outputs(keys, values)
