##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'plugin' """

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import yaml
import time
import logging
import pkg_resources
import yardstick.ssh as ssh

from yardstick.common.task_template import TaskTemplate

LOG = logging.getLogger(__name__)


class Plugin(object):
    """Plugin commands.

       Set of commands to manage plugins.
    """

    def install(self, args):
        """Install a plugin."""

        total_start_time = time.time()
        parser = PluginParser(args.input_file[0])

        plugins, deployment = parser.parse_plugin()
        plugin_name = plugins.get("name")
        print("Installing plugin: %s" % plugin_name)

        LOG.info("Executing _install_setup()")
        self._install_setup(plugin_name, deployment)

        LOG.info("Executing _run()")
        self._run(plugin_name)

        total_end_time = time.time()
        LOG.info("total finished in %d secs",
                 total_end_time - total_start_time)

        print("Done, exiting")

    def remove(self, args):
        """Remove a plugin."""

        total_start_time = time.time()
        parser = PluginParser(args.input_file[0])

        plugins, deployment = parser.parse_plugin()
        plugin_name = plugins.get("name")
        print("Removing plugin: %s" % plugin_name)

        LOG.info("Executing _remove_setup()")
        self._remove_setup(plugin_name, deployment)

        LOG.info("Executing _run()")
        self._run(plugin_name)

        total_end_time = time.time()
        LOG.info("total finished in %d secs",
                 total_end_time - total_start_time)

        print("Done, exiting")

    def _install_setup(self, plugin_name, deployment):
        """Deployment environment setup"""
        target_script = plugin_name + ".bash"
        self.script = pkg_resources.resource_filename(
            'yardstick.resources', 'scripts/install/' + target_script)

        deployment_user = deployment.get("user")
        deployment_ssh_port = deployment.get("ssh_port", ssh.DEFAULT_PORT)
        deployment_ip = deployment.get("ip", None)
        deployment_password = deployment.get("password", None)
        deployment_key_filename = deployment.get("key_filename",
                                                 "/root/.ssh/id_rsa")

        if deployment_ip == "local":
            installer_ip = os.environ.get("INSTALLER_IP", None)

            if deployment_password is not None:
                self._login_via_password(deployment_user, installer_ip,
                                         deployment_password,
                                         deployment_ssh_port)
            else:
                self._login_via_key(self, deployment_user, installer_ip,
                                    deployment_key_filename,
                                    deployment_ssh_port)
        else:
            if deployment_password is not None:
                self._login_via_password(deployment_user, deployment_ip,
                                         deployment_password,
                                         deployment_ssh_port)
            else:
                self._login_via_key(self, deployment_user, deployment_ip,
                                    deployment_key_filename,
                                    deployment_ssh_port)
        # copy script to host
        remotepath = '~/%s.sh' % plugin_name

        LOG.info("copying script to host: %s", remotepath)
        self.client._put_file_shell(self.script, remotepath)

    def _remove_setup(self, plugin_name, deployment):
        """Deployment environment setup"""
        target_script = plugin_name + ".bash"
        self.script = pkg_resources.resource_filename(
            'yardstick.resources', 'scripts/remove/' + target_script)

        deployment_user = deployment.get("user")
        deployment_ssh_port = deployment.get("ssh_port", ssh.DEFAULT_PORT)
        deployment_ip = deployment.get("ip", None)
        deployment_password = deployment.get("password", None)
        deployment_key_filename = deployment.get("key_filename",
                                                 "/root/.ssh/id_rsa")

        if deployment_ip == "local":
            installer_ip = os.environ.get("INSTALLER_IP", None)

            if deployment_password is not None:
                self._login_via_password(deployment_user, installer_ip,
                                         deployment_password,
                                         deployment_ssh_port)
            else:
                self._login_via_key(self, deployment_user, installer_ip,
                                    deployment_key_filename,
                                    deployment_ssh_port)
        else:
            if deployment_password is not None:
                self._login_via_password(deployment_user, deployment_ip,
                                         deployment_password,
                                         deployment_ssh_port)
            else:
                self._login_via_key(self, deployment_user, deployment_ip,
                                    deployment_key_filename,
                                    deployment_ssh_port)

        # copy script to host
        remotepath = '~/%s.sh' % plugin_name

        LOG.info("copying script to host: %s", remotepath)
        self.client._put_file_shell(self.script, remotepath)

    def _login_via_password(self, user, ip, password, ssh_port):
        LOG.info("Log in via pw, user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, password=password, port=ssh_port)
        self.client.wait(timeout=600)

    def _login_via_key(self, user, ip, key_filename, ssh_port):
        LOG.info("Log in via key, user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename,
                              port=ssh_port)
        self.client.wait(timeout=600)

    def _run(self, plugin_name):
        """Run installation script """
        cmd = "sudo bash %s" % plugin_name + ".sh"

        LOG.info("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)


class PluginParser(object):
    """Parser for plugin configration files in yaml format"""

    def __init__(self, path):
        self.path = path

    def parse_plugin(self):
        """parses the plugin file and return a plugins instance
           and a deployment instance
        """

        print("Parsing plugin config:", self.path)

        try:
            kw = {}
            with open(self.path) as f:
                try:
                    input_plugin = f.read()
                    rendered_plugin = TaskTemplate.render(input_plugin, **kw)
                except Exception as e:
                    print("Failed to render template:\n%(plugin)s\n%(err)s\n"
                          % {"plugin": input_plugin, "err": e})
                    raise e
                print("Input plugin is:\n%s\n" % rendered_plugin)

                cfg = yaml.load(rendered_plugin)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "plugin")

        return cfg["plugins"], cfg["deployment"]

    def _check_schema(self, cfg_schema, schema_type):
        """Check if configration file is using the correct schema type"""

        if cfg_schema != "yardstick:" + schema_type + ":0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg_schema))
