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
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios.availability.monitor import basemonitor

LOG = logging.getLogger(__name__)


class MonitorProcess(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "process"

    def setup(self):
        host = self._context[self._config["host"]]

        self.connection = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")
        self.check_script = self.get_script_fullpath(
            "ha_tools/check_process_python.bash")
        self.process_name = self._config["process_name"]

    def monitor_func(self):
        with open(self.check_script, "r") as stdin_file:
            exit_status, stdout, stderr = self.connection.execute(
                "sudo /bin/sh -s {0}".format(self.process_name),
                stdin=stdin_file)

        if not stdout or int(stdout) < self.monitor_data[self.process_name]:
            LOG.info("the (%s) processes are in recovery!", self.process_name)
            return False

        LOG.info("the (%s) processes have been fully recovered!",
                 self.process_name)
        return True

    def verify_SLA(self):
        LOG.debug("the _result:%s", self._result)
        outage_time = self._result.get('outage_time', None)
        max_outage_time = self._config["sla"]["max_recover_time"]
        if outage_time > max_outage_time:
            LOG.error("SLA failure: %f > %f", outage_time, max_outage_time)
            return False
        else:
            LOG.info("the sla is passed")
            return True


def _test():    # pragma: no cover
    host = {
        "ip": "10.20.0.5",
        "user": "root",
        "key_filename": "/root/.ssh/id_rsa"
    }
    context = {"node1": host}
    monitor_configs = []
    config = {
        'monitor_type': 'process',
        'process_name': 'nova-api',
        'host': "node1",
        'monitor_time': 1,
        'sla': {'max_recover_time': 5}
    }
    monitor_configs.append(config)

    p = basemonitor.MonitorMgr()
    p.init_monitors(monitor_configs, context)
    p.start_monitors()
    p.wait_monitors()
    p.verify_SLA()


if __name__ == '__main__':    # pragma: no cover
    _test()
