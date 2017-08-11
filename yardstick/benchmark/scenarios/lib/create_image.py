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


class CreateImage(base.Scenario):
    """Create an OpenStack image"""

    __scenario_type__ = "CreateImage"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.image_name = self.options.get("image_name", "TestImage")
        self.file_path = self.options.get("file_path", None)
        self.disk_format = self.options.get("disk_format", "qcow2")
        self.container_format = self.options.get("container_format", "bare")
        self.min_disk = self.options.get("min_disk", 0)
        self.min_ram = self.options.get("min_ram", 0)
        self.protected = self.options.get("protected", False)
        self.public = self.options.get("public", "public")
        self.tags = self.options.get("tags", [])
        self.custom_property = self.options.get("property", {})

        self.glance_client = op_utils.get_glance_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        image_id = op_utils.create_image(self.glance_client, self.image_name,
                                         self.file_path, self.disk_format,
                                         self.container_format, self.min_disk,
                                         self.min_ram, self.protected, self.tags,
                                         self.public, **self.custom_property)

        if image_id:
            LOG.info("Create image successful!")
            values = [image_id]

        else:
            LOG.info("Create image failed!")
            values = []

        keys = self.scenario_cfg.get('output', '').split()
        return self._push_to_outputs(keys, values)
