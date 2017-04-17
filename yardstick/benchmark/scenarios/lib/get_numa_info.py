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
import subprocess

import yaml
from xml.etree import ElementTree as ET

from yardstick import ssh
from yardstick.benchmark.scenarios import base
from yardstick.common import constants as consts
from yardstick.common.task_template import TaskTemplate

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

        try:
            server = self.options['server']
        except KeyError:
            pass
        else:
            self.server_id = server['id']
            self.host = self._get_current_host_name(self.server_id)

        node_file = os.path.join(consts.YARDSTICK_ROOT_PATH,
                                 self.options.get('file'))

        with open(node_file) as f:
            nodes = yaml.safe_load(TaskTemplate.render(f.read()))
        self.nodes = {a['host_name']: a for a in nodes['nodes']}

    def run(self, result):
        numa_info = self._check_numa_node(self.server_id, self.host)

        keys = self.scenario_cfg.get('output', '').split()
        values = [numa_info]
        return self._push_to_outputs(keys, values)

    def _get_current_host_name(self, server_id):

        key = 'OS-EXT-SRV-ATTR:host'
        cmd = "openstack server show %s | grep %s | awk '{print $4}'" % (
            server_id, key)

        LOG.debug('Executing cmd: %s', cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        current_host = p.communicate()[0].strip()

        LOG.debug('Host: %s', current_host)

        return current_host

    def _get_host_client(self, node_name):
        node = self.nodes.get(node_name, None)
        user = node.get('user', 'ubuntu')
        ssh_port = node.get("ssh_port", ssh.SSH_PORT)
        ip = node.get('ip', None)
        pwd = node.get('password', None)
        key_fname = node.get('key_filename', '/root/.ssh/id_rsa')

        if pwd is not None:
            LOG.debug("Log in via pw, user:%s, host:%s, password:%s",
                      user, ip, pwd)
            self.host_client = ssh.SSH(user, ip, password=pwd, port=ssh_port)
        else:
            LOG.debug("Log in via key, user:%s, host:%s, key_filename:%s",
                      user, ip, key_fname)
            self.host_client = ssh.SSH(user, ip, key_filename=key_fname,
                                       port=ssh_port)

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
