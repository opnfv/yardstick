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

import yardstick.ssh as ssh
from yardstick.common import openstack_utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class AddMemoryLoad(base.Scenario):
    """Add memory load in server
    """

    __scenario_type__ = "AddMemoryLoad"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        self.nova_client = openstack_utils.get_nova_client()

        self.options = scenario_cfg.get('options', {})

        host = self.context_cfg['host']
        user = host.get('user', 'ubuntu')
        port = host.get("ssh_port", ssh.SSH_PORT)
        ip = host.get('ip')
        key_filename = host.get('key_filename', '/root/.ssh/id_rsa')

        self.client = ssh.SSH(user, ip, key_filename=key_filename, port=port)
        self.client.wait(timeout=600)

    def run(self, result):
        self._add_load()

    def _add_load(self):
        try:
            memory_load = self.options['memory_load']
        except KeyError:
            LOG.error('memory_load parameter must be provided')
        else:
            if float(memory_load) == 0:
                return
            cmd = 'free | grep Mem | awk "{print $2}"'
            code, stdout, stderr = self.client.execute(cmd)
            total = int(stdout.split()[1])
            used = int(stdout.split()[2])
            remain_memory = total * float(memory_load) - used
            if remain_memory > 0:
                count = remain_memory / 1024 / 128
                LOG.info('Add %s vm load', count)
                if count != 0:
                    cmd = 'stress -t 10 -m {} --vm-keep'.format(count)
                    self.client.execute(cmd)
