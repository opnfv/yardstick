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


class CreateSecgroup(base.OpenstackScenario):
    """Create an OpenStack security group"""

    __scenario_type__ = "CreateSecgroup"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "sg_name": "yardstick_sec_group",
        "description": None,
    }

    def _run(self, result):
        """execute the test"""

        sg_id = self.neutron_create_security_group_full(sg_name=self.sg_name,
                                                        sg_description=self.description)

        if sg_id:
            result["sg_create"] = 1
            LOG.info("Create security group successful!")
        else:
            result["sg_create"] = 0
            LOG.error("Create security group failed!")

        return [sg_id]
