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


class CreateSecgroup(base.Scenario):
    """Create an OpenStack security group"""

    __scenario_type__ = "CreateSecgroup"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.sg_name = self.options["sg_name"]
        self.description = self.options["description"]
        self.project_id = self.options.get("project_id")
        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        sg_id = openstack_utils.create_security_group_full(
            self.shade_client, self.sg_name, sg_description=self.description,
            project_id=self.project_id)
        if not sg_id:
            result.update({"sg_create": 0})
            LOG.error("Create security group failed!")
            raise exceptions.ScenarioCreateSecurityGroupError

        result.update({"sg_create": 1})
        LOG.info("Create security group successful!")
        keys = self.scenario_cfg.get("output", '').split()
        values = [sg_id]
        return self._push_to_outputs(keys, values)
