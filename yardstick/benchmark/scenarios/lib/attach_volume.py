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


class AttachVolume(base.Scenario):
    """Attach a volmeu to an instance"""

    __scenario_type__ = "AttachVolume"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.server_id = self.options["server_id"]
        self.volume_id = self.options["volume_id"]
        self.device = self.options.get("device")
        self.wait = self.options.get("wait", True)
        self.timeout = self.options.get("timeout", None)
        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = openstack_utils.attach_volume_to_server(
            self.shade_client, self.server_id, self.volume_id,
            device=self.device, wait=self.wait, timeout=self.timeout)

        if not status:
            result.update({"attach_volume": 0})
            LOG.error("Attach volume to server failed!")
            raise exceptions.ScenarioAttachVolumeError

        result.update({"attach_volume": 1})
        LOG.info("Attach volume to server successful!")
