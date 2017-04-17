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
import yardstick.common.openstack_utils as op_utils

LOG = logging.getLogger(__name__)


class GetServer(base.Scenario):
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

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg.get('options', {})

        self.server_id = self.options.get("server_id")
        if self.server_id:
            LOG.debug('Server id is %s', self.server_id)

        default_name = self.scenario_cfg.get('host',
                                             self.scenario_cfg.get('target'))
        self.server_name = self.options.get('server_name', default_name)
        if self.server_name:
            LOG.debug('Server name is %s', self.server_name)

        self.nova_client = op_utils.get_nova_client()

    def run(self, result):
        """execute the test"""

        if self.server_id:
            server = self.nova_client.servers.get(self.server_id)
        else:
            server = op_utils.get_server_by_name(self.server_name)

        keys = self.scenario_cfg.get('output', '').split()

        if server:
            LOG.info("Get server successful!")
            values = [0, self._change_obj_to_dict(server)]
        else:
            LOG.info("Get server failed!")
            values = [1]

        return self._push_to_outputs(keys, values)
