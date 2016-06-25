##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import yardstick.ssh as ssh

import basemonitor as basemonitor
from yardstick.benchmark.scenarios.availability.util import buildshellparams


LOG = logging.getLogger(__name__)


class GeneralMonitor(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "general-monitor"

    def setup(self):
        host = self._context[self._config["host"]]
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")
        self.key = self._config["key"]
        self.monitor_type = self._config["monitor_type"]

        if "parameter" in self._config:
            parameter = self._config['parameter']
            str = buildshellparams(parameter)
            l = list(item for item in parameter.values())
            self.cmd_param = str.format(*l)

        self.monitor_cfg = basemonitor.BaseMonitor.monitor_cfgs.get(self.key)
        self.monitor_script = self.get_script_fullpath(
            self.monitor_cfg['monitor_script'])
        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

    def monitor_func(self):

        if "parameter" in self._config:
            exit_status, stdout, stderr = self.connection.execute(
                self.cmd_param,
                stdin=open(self.monitor_script, "r"))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/bash -s ",
                stdin=open(self.monitor_script, "r"))

        if exit_status:
            return False
        return True

    def verify_SLA(self):
        LOG.debug("the _result:%s" % self._result)
        outage_time = self._result.get('outage_time', None)
        max_outage_time = self._config["sla"]["max_recover_time"]
        if outage_time > max_outage_time:
            LOG.error("SLA failure: %f > %f" % (outage_time, max_outage_time))
            return False
        else:
            return True
