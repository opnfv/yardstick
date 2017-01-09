##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging
import subprocess
import traceback

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.monitor import basemonitor

LOG = logging.getLogger(__name__)


def _execute_shell_command(command):
    '''execute shell script with error handling'''
    exitcode = 0
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
    except Exception:
        exitcode = -1
        output = traceback.format_exc()
        LOG.error("exec command '%s' error:\n ", command)
        LOG.error(traceback.format_exc())

    return exitcode, output


class MonitorOpenstackCmd(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "openstack-cmd"

    def setup(self):
        self.connection = None
        node_name = self._config.get("host", None)
        if node_name:
            host = self._context[node_name]
            ip = host.get("ip", None)
            user = host.get("user", "root")
            ssh_port = host.get("ssh_port", ssh.DEFAULT_PORT)
            key_filename = host.get("key_filename", "~/.ssh/id_rsa")

            self.connection = ssh.SSH(user, ip, key_filename=key_filename,
                                      port=ssh_port)
            self.connection.wait(timeout=600)
            LOG.debug("ssh host success!")

        self.check_script = self.get_script_fullpath(
            "ha_tools/check_openstack_cmd.bash")

        self.cmd = self._config["command_name"]

    def monitor_func(self):
        exit_status = 0
        if self.connection:
            with open(self.check_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "/bin/bash -s '{0}'".format(self.cmd),
                    stdin=stdin_file)

            LOG.debug("the ret stats: %s stdout: %s stderr: %s",
                      exit_status, stdout, stderr)
        else:
            exit_status, stdout = _execute_shell_command(self.cmd)
        if exit_status:
            return False
        return True

    def verify_SLA(self):
        outage_time = self._result.get('outage_time', None)
        LOG.debug("the _result:%s", self._result)
        max_outage_time = self._config["sla"]["max_outage_time"]
        if outage_time > max_outage_time:
            LOG.info("SLA failure: %f > %f", outage_time, max_outage_time)
            return False
        else:
            LOG.info("the sla is passed")
            return True


def _test():    # pragma: no cover
    host = {
        "ip": "192.168.235.22",
        "user": "root",
        "key_filename": "/root/.ssh/id_rsa"
    }
    context = {"node1": host}
    monitor_configs = []
    config = {
        'monitor_type': 'openstack-cmd',
        'command_name': 'nova image-list',
        'monitor_time': 1,
        'host': 'node1',
        'sla': {'max_outage_time': 5}
    }
    monitor_configs.append(config)

    p = basemonitor.MonitorMgr()
    p.init_monitors(monitor_configs, context)
    p.start_monitors()
    p.wait_monitors()
    p.verify_SLA()


if __name__ == '__main__':    # pragma: no cover
    _test()
