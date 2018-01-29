##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging
import os

from yardstick.benchmark.scenarios import base
import yardstick.common.openstack_utils as op_utils


LOG = logging.getLogger(__name__)


class CreateFloatingIp(base.Scenario):
    """Create an OpenStack floating ip"""

    __scenario_type__ = "CreateFloatingIp"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.ext_net_id = os.getenv("EXTERNAL_NETWORK", "external")

        self.neutron_client = op_utils.get_neutron_client()
        self.shade_client = op_utils.get_shade_client()
        self.setup_done = False

    def setup(self):
        """scenario setup"""

        self.setup_done = True

    def run(self, *args):
        """execute the test"""

        if not self.setup_done:
            self.setup()

        net_id = op_utils.get_network_id(self.shade_client, self.ext_net_id)
        floating_info = op_utils.create_floating_ip(self.neutron_client,
                                                    extnet_id=net_id)

        if not floating_info:
            LOG.error("Creating floating ip failed!")
            return

        LOG.info("Creating floating ip successful!")
        keys = self.scenario_cfg.get('output', '').split()
        values = [floating_info["fip_id"], floating_info["fip_addr"]]
        return self._push_to_outputs(keys, values)
