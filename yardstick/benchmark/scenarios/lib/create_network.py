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

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CreateNetwork(base.OpenstackScenario):
    """Create an OpenStack network"""

    __scenario_type__ = "CreateNetwork"
    LOGGER = LOG

    @property
    def params(self):
        return self.options.get("openstack_paras", None)

    def _run(self, result):
        """execute the test"""

        openstack_paras = {'network': self.params}
        network_id = self.neutron_create_neutron_net(openstack_paras)
        if network_id:
            result["network_create"] = 1
            LOG.info("Create network successful!")

        else:
            result["network_create"] = 0
            LOG.error("Create network failed!")

        return [network_id]
