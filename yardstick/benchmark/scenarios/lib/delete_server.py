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


class DeleteServer(base.Scenario):
    """Delete an OpenStack server"""

    __scenario_type__ = "DeleteServer"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']
        self.server_id = self.options["server_id"]
        self.wait = self.options.get("wait", False)
        self.timeout = self.options.get("timeout", 180)
        self.delete_ips = self.options.get("delete_ips", False)
        self.delete_ip_retry = self.options.get("delete_ip_retry", 1)
        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = openstack_utils.delete_instance(
            self.shade_client, self.server_id, wait=self.wait,
            timeout=self.timeout, delete_ips=self.delete_ips,
            delete_ip_retry=self.delete_ip_retry)

        if not status:
            result.update({"delete_server": 0})
            LOG.error("Delete server failed!")
            raise exceptions.ScenarioDeleteServerError

        result.update({"delete_server": 1})
        LOG.info("Delete server successful!")
