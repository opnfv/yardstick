# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this is a modified copy of
# rally/rally/benchmark/scenarios/base.py

""" Scenario base class
"""

from __future__ import absolute_import

import logging
import os
from collections import Mapping

import pkg_resources

from copy import deepcopy

from yardstick import ssh
from yardstick.common import utils
from yardstick.common import openstack_utils
from yardstick.common.constants import YARDSTICK_ROOT_PATH
from yardstick.common.task_template import TaskTemplate
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)


class Scenario(utils.ClassHierarchy):
    """
    Generic root class for Scenarios

    """

    HIERARCHY_TYPE = 'scenario'
    HIERARCHY_NAME = '__scenario_type__'

    __scenario_type__ = 'BaseScenario'
    LOGGER = None
    DEFAULT_OPTIONS = {}

    @classmethod
    def _exec_cmd_with_raise(cls, target, cmd, **kwargs):
        cls.LOGGER.debug("Executing command: %s", cmd)
        return target.execute_with_raise(cmd, **kwargs)

    def __init__(self, scenario_cfg=None, context_cfg=None):
        super(Scenario, self).__init__()
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self._options = None
        self.setup_done = False

    @property
    def options(self):
        if not isinstance(self._options, Mapping):
            self._options = deepcopy(self.scenario_cfg.get('options', {}))
        return self._options

    @options.setter
    def options(self, value):
        if isinstance(self._options, Mapping):
            raise RuntimeError('Options already set')
        if not isinstance(value, Mapping):
            raise RuntimeError('Options value must be a mapping')
        self._options = value

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()

    def _make_output(self, value_iterable):
        if value_iterable is None:
            return {}

        key_iterable = self.scenario_cfg.get('output', '').split()
        return utils.zip_to_dict(key_iterable, value_iterable)

    def _setup(self):
        """scenario setup"""
        pass

    def setup(self):
        """ default impl for scenario setup """
        if self.setup_done:
            return

        self._setup()
        self.setup_done = True

    def _run(self, args):
        """ catcher for not implemented run methods in subclasses """
        raise RuntimeError("run method not implemented")

    def run(self, args):
        """ catcher for not implemented run methods in subclasses """
        self.setup()
        return self._make_output(self._run(args))

    def teardown(self):
        """ default impl for scenario teardown """
        pass

    def __getattr__(self, item):
        if item == '_options':
            # for subclasses that don't call super.__init__!
            self._options = None
            return self._options

        try:
            return self.options[item]
        except KeyError:
            value = self.DEFAULT_OPTIONS[item]
            if isinstance(value, type):
                value = value()
            self.options[item] = value
            return value


class ClientServerScenario(Scenario):
    """
    Base class for Scenarios that use client-server paradigm

    """

    __scenario_type__ = 'ClientServerScenario'
    DEFAULT_DURATION = 20
    MODULE_PATH = ''

    RESOURCE_FILE_MAP = {}

    SSH_DEFAULTS = {}

    @classmethod
    def make_ssh_client(cls, node, timeout=600, overrides=None):
        LOG.info("user:%s, host:%s", node.get('user'), node.get('ip'))
        ssh_client = ssh.SSH.from_node(node, defaults=cls.SSH_DEFAULTS, overrides=overrides)

        ssh_client.wait(timeout=timeout)
        return ssh_client

    @classmethod
    def make_pkg_resource_file_path(cls, file_name, module_path=None):
        if module_path is None:
            module_path = cls.MODULE_PATH
        return pkg_resources.resource_filename(module_path, file_name)

    @classmethod
    def _put_pkg_resource_file(cls, ssh_connection, file_name, dest_name, module_path=None):
        target_script = cls.make_pkg_resource_file_path(file_name, module_path)

        # copy script to client
        ssh_connection.put_file_shell(target_script, dest_name)

    @classmethod
    def _run_pkg_resource_file(cls, ssh_connection, file_name, dest_name, module_path=None):
        target_script = cls.make_pkg_resource_file_path(file_name, module_path)

        # copy script to client
        ssh_connection.put_file_shell(target_script, dest_name)
        return ssh_connection.execute('sudo bash {}'.format(dest_name))

    @classmethod
    def _put_pkg_resource_files(cls, ssh_connection, module_path=None):
        for local_name, remote_name in cls.RESOURCE_FILE_MAP.items():
            cls._put_pkg_resource_file(ssh_connection, local_name, remote_name, module_path)

    @classmethod
    def _run_pkg_resource_files(cls, ssh_connection, module_path=None):
        for local_name, remote_name in cls.RESOURCE_FILE_MAP.items():
            cls._run_pkg_resource_file(ssh_connection, local_name, remote_name, module_path)

    def __init__(self, scenario_cfg, context_cfg, default_server_id=None):
        super(ClientServerScenario, self).__init__(scenario_cfg, context_cfg)
        self.server_id = self.options.get("server_id", default_server_id)
        if self.server_id:
            LOG.debug('Server id is %s', self.server_id)

        self._nodes = None

        self._host_overrides = {}
        self._server_overrides = {}
        self._client_overrides = {}

        self._host_ssh = None
        self._server_ssh = None
        self._client_ssh = None

        target = self.scenario_cfg.get('target')
        default_name = self.scenario_cfg.get('host', target)
        self.server_name = self.options.get('server_name', default_name)
        if self.server_name:
            LOG.debug('Server name is %s', self.server_name)
        self.node_key = self.server_id

    @property
    def duration(self):
        data = self.scenario_cfg.get("runner", self.options)
        default = self.options.get('duration', self.DEFAULT_DURATION)
        return data.get("duration", default)

    @property
    def nodes(self):
        if self._nodes is None:
            file = self.options.get('file')
            node_file = os.path.join(YARDSTICK_ROOT_PATH, file)
            with open(node_file) as f:
                nodes = yaml_load(TaskTemplate.render(f.read()))

            self._nodes = {a['host_name']: a for a in nodes['nodes']}
        return self._nodes

    @property
    def host_data(self):
        return self.nodes.get(self.node_key)

    @property
    def host_client(self):
        if self._host_ssh is None:
            self._host_ssh = self.make_ssh_client(self.host_data, overrides=self._host_overrides)
        return self._host_ssh

    @property
    def server_data(self):
        return self.context_cfg['target']

    @property
    def server_ssh(self):
        if not self._server_ssh:
            self._server_ssh = self.make_ssh_client(self.server_data,
                                                    overrides=self._server_overrides)
        return self._server_ssh

    @property
    def client_data(self):
        return self.context_cfg['host']

    @property
    def client_ssh(self):
        if not self._client_ssh:
            self._client_ssh = self.make_ssh_client(self.client_data,
                                                    overrides=self._client_overrides)
        return self._client_ssh

    def _exec_cmd_to_client_and_server(self, cmd, **kwargs):
        self._exec_cmd_with_raise(self.server_ssh, cmd, **kwargs)
        self._exec_cmd_with_raise(self.client_ssh, cmd, **kwargs)


class OpenstackScenario(ClientServerScenario):
    """
    Base class for Scenarios that operate within an Openstack environment

    """

    SCENARIO_TYPE = 'OpenstackScenario'

    def __init__(self, scenario_cfg, context_cfg, default_server_id=None):
        super(OpenstackScenario, self).__init__(scenario_cfg, context_cfg, default_server_id)

        self._host_name = None
        self._current_server = None
        self._current_server_data = None
        self._nova_client = None
        self._neutron_client = None
        self._glance_client = None
        self._cinder_client = None

    @property
    def host_name(self):
        if self._host_name is None:
            self._host_name = self.current_server_data['OS-EXT-SRV-ATTR:host'].strip()
        return self._host_name

    @property
    def current_server(self):
        if self._current_server is None:
            if self.server_id is not None:
                self._current_server = self.nova_client.servers.get(self.server_id)
            else:
                self._current_server = openstack_utils.get_server_by_name(self.server_name)
        return self._current_server

    @property
    def current_server_data(self):
        if self._current_server_data is None:
            self._current_server_data = utils.change_obj_to_dict(self.current_server)
        return self._current_server_data

    @property
    def nova_client(self):
        if self._nova_client is None:
            self._nova_client = openstack_utils.get_nova_client(patch=True)
        return self._nova_client

    @property
    def neutron_client(self):
        if self._neutron_client is None:
            self._neutron_client = openstack_utils.get_neutron_client(patch=True)
        return self._neutron_client

    @property
    def glance_client(self):
        if self._glance_client is None:
            self._glance_client = openstack_utils.get_glance_client(patch=True)
        return self._glance_client

    @property
    def cinder_client(self):
        if self._cinder_client is None:
            self._cinder_client = openstack_utils.get_cinder_client(patch=True)
        return self._cinder_client

    def __getattr__(self, item):
        client_mapping = {
            'neutron_': 'neutron_client',
            'nova_': 'nova_client',
            'glance_': 'glance_client',
            'cinder_': 'cinder_client',
        }
        for client_type, client_name in client_mapping.items():
            left_extra, _, sub_attr = item.partition(client_type)
            if left_extra:
                continue
            client = getattr(self, client_name)
            return getattr(client, sub_attr)

        return super(OpenstackScenario, self).__getattr__(item)
