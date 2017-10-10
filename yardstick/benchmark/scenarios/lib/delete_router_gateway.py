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


class DeleteRouterGateway(base.OpenstackScenario):
    """Unset an OpenStack router gateway"""

    __scenario_type__ = "DeleteRouterGateway"

    def _run(self, result):
        """execute the test"""

        status = self.neutron_remove_gateway_router(router_id=self.router_id)
        if status:
            result.update({"delete_router_gateway": 1})
            LOG.info("Delete router gateway successful!")
        else:
            result.update({"delete_router_gateway": 0})
            LOG.error("Delete router gateway failed!")
