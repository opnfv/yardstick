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
import time
import logging
import pkg_resources
import yardstick.ssh as ssh

from yardstick.common.task_template import TaskTemplate
from yardstick.common.yaml_loader import yaml_load

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

        deployment_ip = deployment.get("ip", None)

        if deployment_ip == "local":
            self.client = ssh.SSH.from_node(deployment, overrides={
                # host can't be None, fail if no JUMP_HOST_IP
                'ip': os.environ["JUMP_HOST_IP"],
            })
        else:
            self.client = ssh.SSH.from_node(deployment)
        self.client.wait(timeout=600)

        # copy script to host
        remotepath = '~/%s.sh' % plugin_name

        LOG.info("copying script to host: %s", remotepath)
        self.client._put_file_shell(self.script, remotepath)

    def _remove_setup(self, plugin_name, deployment):
        """Deployment environment setup"""
        target_script = plugin_name + ".bash"
        self.script = pkg_resources.resource_filename(
            'yardstick.resources', 'scripts/remove/' + target_script)

        deployment_ip = deployment.get("ip", None)

        if deployment_ip == "local":
            self.client = ssh.SSH.from_node(deployment, overrides={
                # host can't be None, fail if no JUMP_HOST_IP
                'ip': os.environ["JUMP_HOST_IP"],
            })
        else:
            self.client = ssh.SSH.from_node(deployment)
        self.client.wait(timeout=600)

        # copy script to host
        remotepath = '~/%s.sh' % plugin_name

        LOG.info("copying script to host: %s", remotepath)
        self.client._put_file_shell(self.script, remotepath)

    def _run(self, plugin_name):
        """Run installation script """
        cmd = "sudo bash %s" % plugin_name + ".sh"

        LOG.info("Executing command: %s", cmd)
        self.client.execute(cmd)


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

                cfg = yaml_load(rendered_plugin)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "plugin")

        return cfg["plugins"], cfg["deployment"]

    def _check_schema(self, cfg_schema, schema_type):
        """Check if configration file is using the correct schema type"""

        if cfg_schema != "yardstick:" + schema_type + ":0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg_schema))
