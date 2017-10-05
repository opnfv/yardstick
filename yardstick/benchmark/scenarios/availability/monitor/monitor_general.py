##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios.availability.monitor import basemonitor
from yardstick.benchmark.scenarios.availability.util \
    import build_shell_command, execute_shell_command

LOG = logging.getLogger(__name__)


class GeneralMonitor(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "general-monitor"

    def setup(self):
        host = self._context.get(self._config.get('host', None), None)
        self.connection = None
        if host:
            self.connection = ssh.SSH.from_node(
                host, defaults={"user": "root"})
            self.connection.wait(timeout=600)
            LOG.debug("ssh host success!")
        self.key = self._config["key"]
        self.monitor_key = self._config["monitor_key"]
        self.monitor_type = self._config["monitor_type"]
        if "parameter" in self._config:
            self.parameter_config = self._config['parameter']
        self.monitor_cfg = basemonitor.BaseMonitor.monitor_cfgs.get(
            self.monitor_key)
        self.monitor_script = self.get_script_fullpath(
            self.monitor_cfg['monitor_script'])
        LOG.debug("ssh host success!")

    def monitor_func(self):
        if "parameter" in self._config:
            self.cmd_param = \
                build_shell_command(
                    self.parameter_config,
                    bool(self.connection),
                    self.intermediate_variables)
            cmd_remote = "sudo {}".format(self.cmd_param)
            cmd_local = "/bin/bash {0} {1}".format(self.monitor_script, self.cmd_param)
        else:
            cmd_remote = "sudo /bin/sh -s "
            cmd_local = "/bin/bash {0}".format(self.monitor_script)
        if self.connection:
            with open(self.monitor_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(cmd_remote, stdin=stdin_file)
        else:
            exit_status, stdout = execute_shell_command(cmd_local)
        if exit_status:
            return False
        return True

    def verify_SLA(self):
        LOG.debug("the _result:%s", self._result)
        outage_time = self._result.get('outage_time', None)
        max_outage_time = self._config["sla"]["max_outage_time"]
        if outage_time is None:
            LOG.error("There is no outage_time in monitor result.")
            return False
        if outage_time > max_outage_time:
            LOG.error("SLA failure: %f > %f", outage_time, max_outage_time)
            return False
        else:
            return True
