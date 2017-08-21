
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

from yardstick.common import openstack_utils
from yardstick.common.utils import change_obj_to_dict
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class GetMigrateTargetHost(base.Scenario):
    """Get a migrate target host according server
    """

    __scenario_type__ = "GetMigrateTargetHost"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        self.options = self.scenario_cfg.get('options', {})
        default_instance_id = self.options.get('server', {}).get('id', '')
        self.instance_id = self.options.get('server_id', default_instance_id)

        self.nova_client = openstack_utils.get_nova_client()

    def run(self, result):
        current_host = self._get_current_host_name(self.instance_id)
        target_host = self._get_migrate_host(current_host)

        keys = self.scenario_cfg.get('output', '').split()
        values = [target_host]
        return self._push_to_outputs(keys, values)

    def _get_current_host_name(self, server_id):

        return change_obj_to_dict(self.nova_client.servers.get(server_id))['OS-EXT-SRV-ATTR:host']

    def _get_migrate_host(self, current_host):
        hosts = self.nova_client.hosts.list_all()
        compute_hosts = [a.host for a in hosts if a.service == 'compute']
        for host in compute_hosts:
            if host.strip() != current_host.strip():
                return host
