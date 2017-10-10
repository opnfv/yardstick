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


class DeleteFlavor(base.OpenstackScenario):
    """Delete an OpenStack flavor by name"""

    __scenario_type__ = "DeleteFlavor"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "flavor_name": "TestFlavor",
    }

    def _run(self, result):
        """execute the test"""

        self.flavor_id = self.nova_get_flavor_id(self.flavor_name)
        LOG.info("Deleting flavor: %s", self.flavor_name)
        status = self.nova_delete_flavor(self.flavor_id)

        if status:
            LOG.info("Delete flavor successful!")
        else:
            LOG.info("Delete flavor failed!")
