##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from yardstick.common import openstack_utils
from yardstick.common import exceptions
from yardstick.benchmark.scenarios import base


LOG = logging.getLogger(__name__)


class DetachVolume(base.Scenario):
    """Detach a volume from an instance"""

    __scenario_type__ = "DetachVolume"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.server = self.options["server"]
        self.volume = self.options["volume"]
        self.wait = self.options.get("wait", True)
        self.timeout = self.options.get("timeout")

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = openstack_utils.detach_volume(
            self.shade_client, self.server, self.volume, wait=self.wait,
            timeout=self.timeout)

        if not status:
            result.update({"detach_volume": 0})
            LOG.error("Detach volume from server failed!")
            raise exceptions.ScenarioDetachVolumeError

        result.update({"detach_volume": 1})
        LOG.info("Detach volume from server successful!")
