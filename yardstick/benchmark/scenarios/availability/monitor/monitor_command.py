##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import os
import logging
import subprocess

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.monitor import basemonitor

LOG = logging.getLogger(__name__)


def _execute_shell_command(command):
    """execute shell script with error handling"""
    exitcode = 0
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
    except Exception:
        exitcode = -1
        LOG.error("exec command '%s' error:\n ", command, exc_info=True)

    return exitcode, output


class MonitorOpenstackCmd(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "openstack-cmd"

    def setup(self):
        self.connection = None
        node_name = self._config.get("host", None)
        if node_name:
            host = self._context[node_name]

            self.connection = ssh.SSH.from_node(host,
                                                defaults={"user": "root"})
            self.connection.wait(timeout=600)
            LOG.debug("ssh host success!")

        self.check_script = self.get_script_fullpath(
            "ha_tools/check_openstack_cmd.bash")

        self.cmd = self._config["command_name"]

        try:
            insecure = os.environ['OS_INSECURE']
        except KeyError:
            pass
        else:
            if insecure.lower() == "true":
                self.cmd = self.cmd + " --insecure"

    def monitor_func(self):
        exit_status = 0
        exit_status, stdout = _execute_shell_command(self.cmd)
        LOG.debug("Execute command '%s' and the stdout is:\n%s", self.cmd, stdout)
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
