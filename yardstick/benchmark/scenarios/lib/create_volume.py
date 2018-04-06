##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import time
import logging

from yardstick.benchmark.scenarios import base
from yardstick.common import openstack_utils
from yardstick.common import exceptions

LOG = logging.getLogger(__name__)


class CreateVolume(base.Scenario):
    """Create an OpenStack volume"""

    __scenario_type__ = "CreateVolume"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.size = self.options["size"]
        self.wait = self.options.get("wait", True)
        self.timeout = self.options.get("timeout")
        self.image = self.options.get("image")

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        volume = openstack_utils.create_volume(
            self.shade_client, self.size, wait=self.wait, timeout=self.timeout,
            image=self.image)

        if not volume:
            result.update({"volume_create": 0})
            LOG.error("Create volume failed!")
            raise exceptions.ScenarioCreateVolumeError

        status = volume["status"]
        while status == "creating" or status == "downloading":
            LOG.info("Volume status is: %s", status)
            time.sleep(5)
            volume = openstack_utils.get_volume(self.shade_client, self.name)
            status = volume["status"]
        result.update({"volume_create": 1})
        LOG.info("Create volume successful!")
        values = [volume["id"]]
        keys = self.scenario_cfg.get("output", '').split()
        return self._push_to_outputs(keys, values)
