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
    """Attach a volume to an instance

     Parameters:
         server_dict - Server dict
                       e.g.: server_dict: {'id': a1-b2-c3-d4-e6,
                       'status': available, 'name': '', 'attachments': []}
        volume_dict - Volume dict
                       e.g.: volume_dict: {'id': a1-b2-c3-d4-e6,
                       'status': available, 'name': '', 'attachments': []}

    Outputs:
    rc - response code of attach volume to server
        0 for success
        1 for failure
    """

    __scenario_type__ = "AttachVolume"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.server_dict = self.options["server_dict"]
        self.volume_dict = self.options["volume_dict"]
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
            self.shade_client, self.server_dict, self.volume_dict,
            device=self.device, wait=self.wait, timeout=self.timeout)

        if not status:
            result.update({"attach_volume": 0})
            LOG.error("Attach volume to server failed!")
            raise exceptions.ScenarioAttachVolumeError

        result.update({"attach_volume": 1})
        LOG.info("Attach volume to server successful!")
