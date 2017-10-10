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


class GetServer(base.OpenstackScenario):
    """Get a server instance

  Parameters
    server_id - ID of the server
        type:    string
        unit:    N/A
        default: null
    server_name - name of the server
        type:    string
        unit:    N/A
        default: null

    Either server_id or server_name is required.

  Outputs
    rc - response code of getting server instance
        0 for success
        1 for failure
        type:    int
        unit:    N/A
    server - instance of the server
        type:    dict
        unit:    N/A
    """

    __scenario_type__ = "GetServer"
    LOGGER = LOG

    def _run(self, result):
        """execute the test"""

        if self.current_server:
            LOG.info("Get server successful!")
            values = [0, self.current_server_data]
        else:
            LOG.info("Get server failed!")
            values = [1]

        return values
