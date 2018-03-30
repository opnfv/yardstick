##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from yardstick.benchmark.scenarios import base
from yardstick.common import openstack_utils
from yardstick.common import exceptions

LOG = logging.getLogger(__name__)


class GetServer(base.Scenario):
    """Get a server instance

    Parameters:
    server_name_or_id - Name or ID of the server
        type: string
    filters - meta data to use for further filtering
        type: dict
    detailed: Whether or not to add detailed additional information.
        type: bool
    bare: Whether to skip adding any additional information to the server
          record.
        type: bool
    all_projects: Whether to get server from all projects or just the current
                  auth scoped project.
        type: bool

    Outputs:
    rc - response code of getting server instance
        0 for success
        1 for failure
        type:    int
    server - instance of the server
        type:    dict

    """

    __scenario_type__ = 'GetServer'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        default_name = self.scenario_cfg.get('host',
                                             self.scenario_cfg.get('target'))
        self.server_name_or_id = self.options.get('server_name_or_id',
                                                  default_name)
        self.filters = self.options.get('filters')
        self.detailed = self.options.get('detailed', False)
        self.bare = self.options.get('bare', False)
        self.all_projects = self.options.get('all_projects', False)

        self.shade_client = openstack_utils.get_shade_client()

    def run(self, result):
        """execute the test"""

        server = openstack_utils.get_server(
            self.shade_client, name_or_id=self.server_name_or_id,
            filters=self.filters, detailed=self.detailed, bare=self.bare,
            all_projects=self.all_projects)

        if not server:
            result.update({'get_server': 0})
            LOG.error('Get Server failed!')
            raise exceptions.ScenarioGetServerError

        result.update({'get_server': 1})
        LOG.info('Get Server successful!')
        keys = self.scenario_cfg.get('output', '').split()
        server_info = server['server']
        values = [server_info]
        return self._push_to_outputs(keys, values)
