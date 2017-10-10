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


class CreateSubnet(base.OpenstackScenario):
    """Create an OpenStack flavor"""

    __scenario_type__ = "CreateSubnet"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "openstack_paras": None,
    }

    def _run(self, result):
        """execute the test"""

        openstack_paras = {'subnets': [self.openstack_paras]}
        subnet_id = self.neutron_create_subnet(openstack_paras)

        if subnet_id:
            result["subnet_create"] = 1
            LOG.info("Create subnet successful!")
        else:
            result["subnet_create"] = 0
            LOG.error("Create subnet failed!")

        return [subnet_id]
