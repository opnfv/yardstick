##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging
import os

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CreateFloatingIp(base.OpenstackScenario):
    """Create an OpenStack floating ip"""

    __scenario_type__ = "CreateFloatingIp"
    LOGGER = LOG

    def __init__(self, scenario_cfg, context_cfg):
        super(CreateFloatingIp, self).__init__(scenario_cfg, context_cfg)

        self.ext_net_id = os.getenv("EXTERNAL_NETWORK", "external")

    def _run(self, result):
        """execute the test"""

        net_id = self.neutron_get_network_id(self.ext_net_id)
        floating_info = self.neutron_create_floating_ip(extnet_id=net_id)

        try:
            values = [floating_info["fip_id"], floating_info["fip_addr"]]
        except KeyError:
            LOG.error("Creating floating ip failed!")
            return []
        else:
            LOG.info("Creating floating ip successful!")
            return values
