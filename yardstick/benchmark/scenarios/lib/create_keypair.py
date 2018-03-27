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


class CreateKeypair(base.Scenario):
    """Create an OpenStack keypair"""

    __scenario_type__ = "CreateKeypair"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.name = self.options["key_name"]
        self.public_key = self.options.get("public_key")
        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        keypair = openstack_utils.create_keypair(
            self.shade_client, self.name, public_key=self.public_key)

        if not keypair:
            result.update({"keypair_create": 0})
            LOG.error("Create keypair failed!")
            raise exceptions.ScenarioCreateKeypairError

        result.update({"keypair_create": 1})
        LOG.info("Create keypair successful!")
        keys = self.scenario_cfg.get('output', '').split()
        keypair_id = keypair['keypair']['id']
        values = [keypair_id]
        return self._push_to_outputs(keys, values)
