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


class DeleteRouterInterface(base.OpenstackScenario):
    """Unset an OpenStack router interface"""

    __scenario_type__ = "DeleteRouterInterface"

    def _run(self, result):
        """execute the test"""

        status = self.neutron_remove_interface_router(router_id=self.router_id,
                                                      subnet_id=self.subnet_id)
        if status:
            result.update({"delete_router_interface": 1})
            LOG.info("Delete router interface successful!")
        else:
            result.update({"delete_router_interface": 0})
            LOG.error("Delete router interface failed!")
