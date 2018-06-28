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


class DeleteKeypair(base.Scenario):
    """Delete an OpenStack keypair"""

    __scenario_type__ = "DeleteKeypair"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.key_name = self.options["key_name"]

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        status = openstack_utils.delete_keypair(self.shade_client,
                                                self.key_name)

        if not status:
            result.update({"delete_keypair": 0})
            LOG.error("Delete keypair failed!")
            raise exceptions.ScenarioDeleteKeypairError

        result.update({"delete_keypair": 1})
        LOG.info("Delete keypair successful!")
