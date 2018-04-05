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


class GetFlavor(base.Scenario):
    """Get an OpenStack flavor by name"""

    __scenario_type__ = "GetFlavor"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]
        self.name_or_id = self.options["flavor_name_or_id"]
        self.filters = self.options.get("filters")
        self.get_extra = self.options.get("get_extra", True)
        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        LOG.info("Querying flavor: %s", self.name_or_id)
        flavor = openstack_utils.get_flavor(
            self.shade_client, self.name_or_id, filters=self.filters,
            get_extra=self.get_extra)

        if not flavor:
            result.update({"get_flavor": 0})
            LOG.error("Get flavor failed!")
            raise exceptions.ScenarioGetFlavorError

        result.update({"get_flavor": 1})
        LOG.info("Get flavor successful!")
        values = [flavor]
        keys = self.scenario_cfg.get("output", '').split()
        return self._push_to_outputs(keys, values)
