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


class DeleteFloatingIp(base.OpenstackScenario):
    """Delete an OpenStack floating ip """

    __scenario_type__ = "DeleteFloatingIp"

    def _run(self, result):
        """execute the test"""

        status = self.nova_delete_floating_ip(floatingip_id=self.floating_ip_id)
        if status:
            result.update({"delete_floating_ip": 1})
            LOG.info("Delete floating ip successful!")
        else:
            result.update({"delete_floating_ip": 0})
            LOG.error("Delete floating ip failed!")
