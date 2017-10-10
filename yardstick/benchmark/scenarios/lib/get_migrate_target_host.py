
# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class GetMigrateTargetHost(base.OpenstackScenario):
    """Get a migrate target host according server
    """

    __scenario_type__ = "GetMigrateTargetHost"
    LOGGER = LOG

    def __init__(self, scenario_cfg, context_cfg, default_server_id=None):
        if default_server_id is None:
            default_server_id = scenario_cfg.get('options', {}).get('server', {}).get('id', '')
        super(GetMigrateTargetHost, self).__init__(scenario_cfg, context_cfg, default_server_id)

    def _run(self, result):
        return [self._get_migrate_host()]

    def _get_migrate_host(self):
        hosts = self.nova_client.hosts.list_all()
        compute_hosts = (a.host for a in hosts if a.service == 'compute')
        for host in compute_hosts:
            if host.strip() != self.host_name:
                return host
