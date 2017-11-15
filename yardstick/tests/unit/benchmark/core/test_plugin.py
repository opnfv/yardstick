##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy
import os
import pkg_resources

import mock
import testtools

from yardstick import ssh
from yardstick.benchmark.core import plugin
from yardstick.tests import fixture


class PluginTestCase(testtools.TestCase):

    FILE = """
schema: "yardstick:plugin:0.1"

plugins:
    name: sample

deployment:
    ip: 10.1.0.50
    user: root
    password: root
"""

    NAME = 'sample'
    DEPLOYMENT = {'ip': '10.1.0.50', 'user': 'root', 'password': 'root'}

    def setUp(self):
        super(PluginTestCase, self).setUp()
        self.plugin_parser = plugin.PluginParser(mock.Mock())
        self.plugin = plugin.Plugin()
        self.useFixture(fixture.PluginParserFixture(PluginTestCase.FILE))

        self._mock_ssh_from_node = mock.patch.object(ssh.SSH, 'from_node')
        self.mock_ssh_from_node = self._mock_ssh_from_node.start()
        self.mock_ssh_obj = mock.Mock()
        self.mock_ssh_from_node.return_value = self.mock_ssh_obj
        self.mock_ssh_obj.wait = mock.Mock()
        self.mock_ssh_obj._put_file_shell = mock.Mock()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self._mock_ssh_from_node.stop()

    def test_install(self):
        args = mock.Mock()
        args.input_file = [mock.Mock()]
        with mock.patch.object(self.plugin, '_install_setup') as \
                mock_install, \
                mock.patch.object(self.plugin, '_run') as mock_run:
            self.plugin.install(args)
            mock_install.assert_called_once_with(PluginTestCase.NAME,
                                                 PluginTestCase.DEPLOYMENT)
            mock_run.assert_called_once_with(PluginTestCase.NAME)

    def test_remove(self):
        args = mock.Mock()
        args.input_file = [mock.Mock()]
        with mock.patch.object(self.plugin, '_remove_setup') as \
                mock_remove, \
                mock.patch.object(self.plugin, '_run') as mock_run:
            self.plugin.remove(args)
            mock_remove.assert_called_once_with(PluginTestCase.NAME,
                                                PluginTestCase.DEPLOYMENT)
            mock_run.assert_called_once_with(PluginTestCase.NAME)

    @mock.patch.object(pkg_resources, 'resource_filename',
                       return_value='script')
    def test__install_setup(self, mock_resource_filename):
        plugin_name = 'plugin_name'
        self.plugin._install_setup(plugin_name, PluginTestCase.DEPLOYMENT)
        mock_resource_filename.assert_called_once_with(
            'yardstick.resources', 'scripts/install/' + plugin_name + '.bash')
        self.mock_ssh_from_node.assert_called_once_with(
            PluginTestCase.DEPLOYMENT)
        self.mock_ssh_obj.wait.assert_called_once_with(timeout=600)
        self.mock_ssh_obj._put_file_shell.assert_called_once_with(
            'script', '~/{0}.sh'.format(plugin_name))

    @mock.patch.object(pkg_resources, 'resource_filename',
                       return_value='script')
    @mock.patch.object(os, 'environ', return_value='1.2.3.4')
    def test__install_setup_with_ip_local(self, mock_os_environ,
                                          mock_resource_filename):
        plugin_name = 'plugin_name'
        deployment = copy.deepcopy(PluginTestCase.DEPLOYMENT)
        deployment['ip'] = 'local'
        self.plugin._install_setup(plugin_name, deployment)
        mock_os_environ.__getitem__.assert_called_once_with('JUMP_HOST_IP')
        mock_resource_filename.assert_called_once_with(
            'yardstick.resources',
            'scripts/install/' + plugin_name + '.bash')
        self.mock_ssh_from_node.assert_called_once_with(
            deployment, overrides={'ip': os.environ["JUMP_HOST_IP"]})
        self.mock_ssh_obj.wait.assert_called_once_with(timeout=600)
        self.mock_ssh_obj._put_file_shell.assert_called_once_with(
            'script', '~/{0}.sh'.format(plugin_name))

    @mock.patch.object(pkg_resources, 'resource_filename',
                       return_value='script')
    def test__remove_setup(self, mock_resource_filename):
        plugin_name = 'plugin_name'
        self.plugin._remove_setup(plugin_name, PluginTestCase.DEPLOYMENT)
        mock_resource_filename.assert_called_once_with(
            'yardstick.resources',
            'scripts/remove/' + plugin_name + '.bash')
        self.mock_ssh_from_node.assert_called_once_with(
            PluginTestCase.DEPLOYMENT)
        self.mock_ssh_obj.wait.assert_called_once_with(timeout=600)
        self.mock_ssh_obj._put_file_shell.assert_called_once_with(
            'script', '~/{0}.sh'.format(plugin_name))

    @mock.patch.object(pkg_resources, 'resource_filename',
                       return_value='script')
    @mock.patch.object(os, 'environ', return_value='1.2.3.4')
    def test__remove_setup_with_ip_local(self, mock_os_environ,
                                         mock_resource_filename):
        plugin_name = 'plugin_name'
        deployment = copy.deepcopy(PluginTestCase.DEPLOYMENT)
        deployment['ip'] = 'local'
        self.plugin._remove_setup(plugin_name, deployment)
        mock_os_environ.__getitem__.assert_called_once_with('JUMP_HOST_IP')
        mock_resource_filename.assert_called_once_with(
            'yardstick.resources',
            'scripts/remove/' + plugin_name + '.bash')
        self.mock_ssh_from_node.assert_called_once_with(
            deployment, overrides={'ip': os.environ["JUMP_HOST_IP"]})
        self.mock_ssh_obj.wait.assert_called_once_with(timeout=600)
        self.mock_ssh_obj._put_file_shell.mock_os_environ(
            'script', '~/{0}.sh'.format(plugin_name))
