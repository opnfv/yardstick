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


class DeleteServer(base.OpenstackScenario):
    """Delete an OpenStack server"""

    __scenario_type__ = "DeleteServer"
    LOGGER = LOG
    DEFAULT_OPTIONS = {
        "server_id": None,
    }

    def _run(self, result):
        """execute the test"""

        status = self.nova_delete_instance(instance_id=self.server_id)
        if status:
            LOG.info("Delete server successful!")
        else:
            LOG.error("Delete server failed!")
