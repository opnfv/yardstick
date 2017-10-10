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
from yardstick.common.utils import change_obj_to_dict

LOG = logging.getLogger(__name__)


class GetFlavor(base.OpenstackScenario):
    """Get an OpenStack flavor by name"""

    __scenario_type__ = "GetFlavor"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "flavor_name": "TestFlavor",
    }

    def _run(self, result):
        """execute the test"""

        LOG.info("Querying flavor: %s", self.flavor_name)
        flavor = self.nova_get_flavor_by_name(self.flavor_name)
        if flavor:
            LOG.info("Get flavor successful!")
            values = [change_obj_to_dict(flavor)]
        else:
            LOG.info("Get flavor: no flavor matched!")
            values = []

        return values
