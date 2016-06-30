##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'plugin' """

import sys
import yaml
import time
import logging
import pkg_resources
import yardstick.ssh as ssh

from yardstick.common.utils import cliargs
from yardstick.common.task_template import TaskTemplate

LOG = logging.getLogger(__name__)


class PluginCommands(object):
    '''Plugin commands.

       Set of commands to manage plugins.
    '''

    @cliargs("input_file", type=str, help="path to plugin configuration file",
             nargs=1)
    def do_install(self, args):
        '''Install a plugin.'''

        total_start_time = time.time()
        parser = PluginParser(args.input_file[0])

        plugins, deployment = parser.parse_plugin()
        plugin_name = plugins.get("name")
        print("Installing plugin: %s" % plugin_name)

        self._install_setup(plugin_name, deployment)

        self._run(plugin_name)

        total_end_time = time.time()
        LOG.info("total finished in %d secs",
                 total_end_time - total_start_time)

        print("Done, exiting")

    def do_remove(self, args):
        '''Remove a plugin.'''

        total_start_time = time.time()
        parser = PluginParser(args.input_file[0])

        plugins, deployment = parser.parse_plugin()
        plugin_name = plugins.get("name")
        print("Remove plugin: %s" % plugin_name)

        self._remove_setup(plugin_name, deployment)

        self._run(plugin_name)

        total_end_time = time.time()
        LOG.info("total finished in %d secs",
                 total_end_time - total_start_time)

        print("Done, exiting")

    def _install_setup(self, plugin_name, deployment):
        '''Deployment environment setup'''
        target_script = plugin_name + ".bash"
        self.script = pkg_resources.resource_filename(
            'yardstick.resources', 'script/install/' + target_script)

        deployment_user = deployment.get("user")
        deployment_ip = deployment.get("ip")

        deployment_password = deployment.get("password")
        LOG.debug("user:%s, host:%s", deployment_user, deployment_ip)
        self.client = ssh.SSH(deployment_user, deployment_ip,
                              password=deployment_password)
        self.client.wait(timeout=600)

        # copy script to host
        cmd = "cat > ~/%s.sh" % plugin_name
        self.client.run(cmd, stdin=open(self.script, 'rb'))

    def _remove_setup(self, plugin_name, deployment):
        '''Deployment environment setup'''
        target_script = plugin_name + ".bash"
        self.script = pkg_resources.resource_filename(
            'yardstick.resources', 'script/remove/' + target_script)

        deployment_user = deployment.get("user")
        deployment_ip = deployment.get("ip")

        deployment_password = deployment.get("password")
        LOG.debug("user:%s, host:%s", deployment_user, deployment_ip)
        self.client = ssh.SSH(deployment_user, deployment_ip,
                              password=deployment_password)
        self.client.wait(timeout=600)

        # copy script to host
        cmd = "cat > ~/%s.sh" % plugin_name
        self.client.run(cmd, stdin=open(self.script, 'rb'))

    def _run(self, plugin_name):
        '''Run installation script '''
        cmd = "sudo bash %s" % plugin_name + ".sh"

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)


class PluginParser(object):
    '''Parser for plugin configration files in yaml format'''
    def __init__(self, path):
        self.path = path

    def parse_plugin(self):
        '''parses the plugin file and return a plugins instance
           and a deployment instance
        '''

        print "Parsing plugin config:", self.path

        try:
            kw = {}
            with open(self.path) as f:
                try:
                    input_plugin = f.read()
                    rendered_plugin = TaskTemplate.render(input_plugin, **kw)
                except Exception as e:
                    print(("Failed to render template:\n%(plugin)s\n%(err)s\n")
                          % {"plugin": input_plugin, "err": e})
                    raise e
                print(("Input plugin is:\n%s\n") % rendered_plugin)

                cfg = yaml.load(rendered_plugin)
        except IOError as ioerror:
            sys.exit(ioerror)

        self._check_schema(cfg["schema"], "plugin")

        return cfg["plugins"], cfg["deployment"]

    def _check_schema(self, cfg_schema, schema_type):
        '''Check if configration file is using the correct schema type'''

        if cfg_schema != "yardstick:" + schema_type + ":0.1":
            sys.exit("error: file %s has unknown schema %s" % (self.path,
                                                               cfg_schema))
