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
import os

from xml.etree import ElementTree as ET

from yardstick import ssh
from yardstick.benchmark.scenarios import base
from yardstick.common import constants as consts
from yardstick.common.utils import change_obj_to_dict
from yardstick.common.openstack_utils import get_nova_client
from yardstick.common.task_template import TaskTemplate
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)


class GetNumaInfo(base.Scenario):
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "GetNumaInfo"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg.get('options', {})

        server = self.options['server']
        self.server_id = server['id']
        self.host = self._get_current_host_name(self.server_id)

        node_file = os.path.join(consts.YARDSTICK_ROOT_PATH,
                                 self.options.get('file'))

        with open(node_file) as f:
            nodes = yaml_load(TaskTemplate.render(f.read()))
        self.nodes = {a['host_name']: a for a in nodes['nodes']}

    def run(self, result):
        numa_info = self._check_numa_node(self.server_id, self.host)

        keys = self.scenario_cfg.get('output', '').split()
        values = [numa_info]
        return self._push_to_outputs(keys, values)

    def _get_current_host_name(self, server_id):

        return change_obj_to_dict(get_nova_client().servers.get(server_id))['OS-EXT-SRV-ATTR:host']

    def _get_host_client(self, node_name):
        self.host_client = ssh.SSH.from_node(self.nodes.get(node_name))
        self.host_client.wait(timeout=600)

    def _check_numa_node(self, server_id, host):
        self._get_host_client(host)

        cmd = "sudo virsh dumpxml %s" % server_id
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.host_client.execute(cmd)
        if status:
            raise RuntimeError(stderr)
        root = ET.fromstring(stdout)
        vcpupin = [a.attrib for a in root.iter('vcpupin')]
        pinning = [a.attrib for a in root.iter('memnode')]
        return {"pinning": pinning, 'vcpupin': vcpupin}
