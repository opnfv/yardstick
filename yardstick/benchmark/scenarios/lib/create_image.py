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


class CreateImage(base.Scenario):
    """Create an OpenStack image"""

    __scenario_type__ = "CreateImage"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.name = self.options["image_name"]
        self.file_name = self.options.get("file_name")
        self.container = self.options.get("container", 'images')
        self.md5 = self.options.get("md5")
        self.sha256 = self.options.get("sha256")
        self.disk_format = self.options.get("disk_format")
        self.container_format = self.options.get("container_format",)
        self.disable_vendor_agent = self.options.get("disable_vendor_agent", True)
        self.wait = self.options.get("wait", True)
        self.timeout = self.options.get("timeout", 3600)
        self.allow_duplicates = self.options.get("allow_duplicates", False)
        self.meta = self.options.get("meta")
        self.volume = self.options.get("volume")

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        image_id = openstack_utils.create_image(
            self.shade_client, self.name, filename=self.file_name,
            container=self.container, md5=self.md5, sha256=self.sha256,
            disk_format=self.disk_format,
            container_format=self.container_format,
            disable_vendor_agent=self.disable_vendor_agent, wait=self.wait,
            timeout=self.timeout, allow_duplicates=self.allow_duplicates,
            meta=self.meta, volume=self.volume)

        if not image_id:
            result.update({"image_create": 0})
            LOG.error("Create image failed!")
            raise exceptions.ScenarioCreateImageError

        result.update({"image_create": 1})
        LOG.info("Create image successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [image_id]
        return self._push_to_outputs(keys, values)
