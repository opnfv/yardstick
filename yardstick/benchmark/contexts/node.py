##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import subprocess
import os
import collections
import logging
import tempfile

import six
import pkg_resources

from yardstick import ssh
from yardstick.benchmark.contexts.base import Context
from yardstick.common.constants import ANSIBLE_DIR, YARDSTICK_ROOT_PATH
from yardstick.common.ansible_common import AnsibleCommon
from yardstick.common.exceptions import ContextUpdateCollectdForNodeError

LOG = logging.getLogger(__name__)

DEFAULT_DISPATCH = 'script'


class NodeContext(Context):
    """Class that handle nodes info"""

    __context_type__ = "Node"

    def __init__(self):
        self.file_path = None
        self.nodes = []
        self.networks = {}
        self.controllers = []
        self.computes = []
        self.baremetals = []
        self.env = {}
        self.attrs = {}
        self.DISPATCH_TYPES = {
            "ansible": self._dispatch_ansible,
            "script": self._dispatch_script,
        }
        super(NodeContext, self).__init__()

    def init(self, attrs):
        """initializes itself from the supplied arguments"""
        super(NodeContext, self).init(attrs)

        cfg = self.read_pod_file(attrs)

        self.env = attrs.get('env', {})
        self.attrs = attrs
        LOG.debug("Env: %r", self.env)

        # add optional static network definition
        self.networks.update(cfg.get("networks", {}))

    def deploy(self):
        config_type = self.env.get('type', DEFAULT_DISPATCH)
        self.DISPATCH_TYPES[config_type]("setup")

    def undeploy(self):
        config_type = self.env.get('type', DEFAULT_DISPATCH)
        self.DISPATCH_TYPES[config_type]("teardown")
        super(NodeContext, self).undeploy()

    def _dispatch_script(self, key):
        steps = self.env.get(key, [])
        for step in steps:
            for host, info in step.items():
                self._execute_script(host, info)

    def _dispatch_ansible(self, key):
        try:
            playbooks = self.env[key]
        except KeyError:
            pass
        else:
            self._do_ansible_job(playbooks)

    def _do_ansible_job(self, playbooks):
        self.ansible_exec = AnsibleCommon(nodes=self.nodes,
                                          test_vars=self.env)
        # playbooks relative to ansible dir
        # playbooks can also be a list of playbooks
        self.ansible_exec.gen_inventory_ini_dict()
        if isinstance(playbooks, six.string_types):
            playbooks = [playbooks]
        playbooks = [self.fix_ansible_path(playbook) for playbook in playbooks]

        tmpdir = tempfile.mkdtemp(prefix='ansible-')
        self.ansible_exec.execute_ansible(playbooks, tmpdir,
                                          verbose=self.env.get("verbose",
                                                               False))

    def fix_ansible_path(self, playbook):
        if not os.path.isabs(playbook):
            #  make relative paths absolute in ANSIBLE_DIR
            playbook = os.path.join(ANSIBLE_DIR, playbook)
        return playbook

    def _get_physical_nodes(self):
        return self.nodes

    def _get_physical_node_for_server(self, server_name):

        node_name, context_name = self.split_host_name(server_name)

        if context_name is None or self.name != context_name:
            return None

        for n in (n for n in self.nodes if n["name"] == node_name):
            return "{}.{}".format(n["name"], self._name)

        return None

    def update_collectd_options_for_node(self, options, attr_name):
        node_name, _ = self.split_host_name(attr_name)

        matching_nodes = (n for n in self.nodes if n["name"] == node_name)
        try:
            node = next(matching_nodes)
        except StopIteration:
            raise ContextUpdateCollectdForNodeError(attr_name=attr_name)

        node["collectd"] = options

    def _get_server(self, attr_name):
        """lookup server info by name from context
        attr_name: a name for a server listed in nodes config file
        """
        node_name, name = self.split_host_name(attr_name)
        if name is None or self.name != name:
            return None

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
            raise ValueError("Duplicate nodes!!! Nodes: %s %s" %
                             (node, duplicate))

        node["name"] = attr_name
        node.setdefault("interfaces", {})
        return node

    def _get_network(self, attr_name):
        if not isinstance(attr_name, collections.Mapping):
            network = self.networks.get(attr_name)

        else:
            # Don't generalize too much  Just support vld_id
            vld_id = attr_name.get('vld_id', {})
            # for node context networks are dicts
            iter1 = (n for n in self.networks.values() if n.get('vld_id') == vld_id)
            network = next(iter1, None)

        if network is None:
            return None

        result = {
            # name is required
            "name": network["name"],
            "vld_id": network.get("vld_id"),
            "segmentation_id": network.get("segmentation_id"),
            "network_type": network.get("network_type"),
            "physical_network": network.get("physical_network"),
        }
        return result

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
        status, _, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

    def _execute_local_script(self, info):
        script, options = self._get_script(info)
        script = os.path.join(YARDSTICK_ROOT_PATH, script)
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
