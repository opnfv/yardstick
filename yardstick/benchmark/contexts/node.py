##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import errno
import subprocess
import os
import collections
import logging

import yaml
import pkg_resources

from yardstick import ssh
from yardstick.benchmark.contexts.base import Context
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)


class NodeContext(Context):
    """Class that handle nodes info"""

    __context_type__ = "Node"

    def __init__(self):
        self.name = None
        self.file_path = None
        self.nodes = []
        self.controllers = []
        self.computes = []
        self.baremetals = []
        self.env = {}
        self.attrs = {}
        super(NodeContext, self).__init__()

    def read_config_file(self):
        """Read from config file"""

        with open(self.file_path) as stream:
            LOG.info("Parsing pod file: %s", self.file_path)
            cfg = yaml.load(stream)
        return cfg

    def init(self, attrs):
        """initializes itself from the supplied arguments"""
        self.name = attrs["name"]
        self.file_path = attrs.get("file", "pod.yaml")

        try:
            cfg = self.read_config_file()
        except IOError as ioerror:
            if ioerror.errno == errno.ENOENT:
                self.file_path = \
                    os.path.join(consts.YARDSTICK_ROOT_PATH, self.file_path)
                cfg = self.read_config_file()
            else:
                raise

        self.nodes.extend(cfg["nodes"])
        self.controllers.extend([node for node in cfg["nodes"]
                                 if node["role"] == "Controller"])
        self.computes.extend([node for node in cfg["nodes"]
                              if node["role"] == "Compute"])
        self.baremetals.extend([node for node in cfg["nodes"]
                                if node["role"] == "Baremetal"])
        LOG.debug("Nodes: %r", self.nodes)
        LOG.debug("Controllers: %r", self.controllers)
        LOG.debug("Computes: %r", self.computes)
        LOG.debug("BareMetals: %r", self.baremetals)

        self.env = attrs.get('env', {})
        self.attrs = attrs
        LOG.debug("Env: %r", self.env)

    def deploy(self):
        config_type = self.env.get('type', '')
        if config_type == 'ansible':
            self._dispatch_ansible('setup')
        elif config_type == 'script':
            self._dispatch_script('setup')

    def undeploy(self):
        config_type = self.env.get('type', '')
        if config_type == 'ansible':
            self._dispatch_ansible('teardown')
        elif config_type == 'script':
            self._dispatch_script('teardown')
        super(NodeContext, self).undeploy()

    def _dispatch_script(self, key):
        steps = self.env.get(key, [])
        for step in steps:
            for host, info in step.items():
                self._execute_script(host, info)

    def _dispatch_ansible(self, key):
        try:
            step = self.env[key]
        except KeyError:
            pass
        else:
            self._do_ansible_job(step)

    def _do_ansible_job(self, path):
        cmd = 'ansible-playbook -i inventory.ini %s' % path
        p = subprocess.Popen(cmd, shell=True, cwd=consts.ANSIBLE_DIR)
        p.communicate()

    def _get_context_from_server(self, name):
        """lookup server info for a given nodename
        name: a name for a server listed in nodes and get its attributes
        """

        if isinstance(name, collections.Mapping):
            return None

        if self.name != name.split(".")[1]:
            return None

        return self.attrs

    def _get_server(self, attr_name):
        """lookup server info by name from context
        attr_name: a name for a server listed in nodes config file
        """
        if isinstance(attr_name, collections.Mapping):
            return None

        if self.name != attr_name.split(".")[1]:
            return None
        node_name = attr_name.split(".")[0]
        matching_nodes = (n for n in self.nodes if n["name"] == node_name)

        try:
            # A clone is created in order to avoid affecting the
            # original one.
            node = dict(next(matching_nodes))
        except StopIteration:
            return None

        try:
            duplicate = next(matching_nodes)
        except StopIteration:
            pass
        else:
            raise ValueError("Duplicate nodes!!! Nodes: %s %s",
                             (matching_nodes, duplicate))

        node["name"] = attr_name
        return node

    def _execute_script(self, node_name, info):
        if node_name == 'local':
            self._execute_local_script(info)
        else:
            self._execute_remote_script(node_name, info)

    def _execute_remote_script(self, node_name, info):
        prefix = self.env.get('prefix', '')
        script, options = self._get_script(info)

        script_file = pkg_resources.resource_filename(prefix, script)

        self._get_client(node_name)
        self.client._put_file_shell(script_file, '~/{}'.format(script))

        cmd = 'sudo bash {} {}'.format(script, options)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

    def _execute_local_script(self, info):
        script, options = self._get_script(info)
        script = os.path.join(consts.YARDSTICK_ROOT_PATH, script)
        cmd = ['bash', script, options]

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        LOG.debug('\n%s', p.communicate()[0])

    def _get_script(self, info):
        return info.get('script'), info.get('options', '')

    def _get_client(self, node_name):
        node = self._get_node_info(node_name.strip())

        if node is None:
            raise SystemExit('No such node')

        self.client = ssh.SSH.from_node(node, defaults={'user': 'ubuntu'})

        self.client.wait(timeout=600)

    def _get_node_info(self, name):
        return next((n for n in self.nodes if n['name'].strip() == name))
