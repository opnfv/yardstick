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


class CreateFloatingIp(base.Scenario):
    """Create an OpenStack floating ip"""

    __scenario_type__ = "CreateFloatingIp"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        self.network_name_or_id = self.options.get("network_name_or_id")
        self.server = self.options.get("server")
        self.fixed_address = self.options.get("fixed_address")
        self.nat_destination = self.options.get("nat_destination")
        self.port = self.options.get("port")
        self.wait = self.options.get("wait", False)
        self.timeout = self.options.get("timeout", 60)

        self.shade_client = openstack_utils.get_shade_client()

        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, result):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        floating_info = openstack_utils.create_floating_ip(
            self.shade_client, network_name_or_id=self.network_name_or_id,
            server=self.server, fixed_address=self.fixed_address,
            nat_destination=self.nat_destination, port=self.port,
            wait=self.wait, timeout=self.timeout)

        if not floating_info:
            result.update({"floating_ip_create": 0})
            LOG.error("Creating floating ip failed!")
            raise exceptions.ScenarioCreateFloatingIPError

        result.update({"floating_ip_create": 1})
        LOG.info("Creating floating ip successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [floating_info["fip_id"], floating_info["fip_addr"]]
        return self._push_to_outputs(keys, values)
