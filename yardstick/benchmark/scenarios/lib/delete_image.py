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


class DeleteImage(base.Scenario):
    """Delete an OpenStack image"""

    __scenario_type__ = "DeleteImage"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.image_name_or_id = self.options["image_name_or_id"]
        self.wait = self.options.get("wait", False)
        self.timeout = self.options.get("timeout", 3600)
        self.delete_objects = self.options.get("delete_objects", True)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = openstack_utils.delete_image(
            self.shade_client, self.image_name_or_id, wait=self.wait,
            timeout=self.timeout, delete_objects=self.delete_objects)

        if not status:
            result.update({"delete_image": 0})
            LOG.error("Delete image failed!")
            raise exceptions.ScenarioDeleteImageError

        result.update({"delete_image": 1})
        LOG.info("Delete image successful!")
