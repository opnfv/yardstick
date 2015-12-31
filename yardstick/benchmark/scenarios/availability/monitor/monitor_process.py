##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import yardstick.ssh as ssh

import basemonitor as basemonitor

LOG = logging.getLogger(__name__)


class MonitorProcess(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "process"

    def setup(self):
        host = self._context[self._config["host"]]
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")

        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")
        self.check_script = self.get_script_fullpath(
            "ha_tools/check_process_python.bash")
        self.process_name = self._config["process_name"]

    def monitor_func(self):
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(self.process_name),
            stdin=open(self.check_script, "r"))
        if not stdout or int(stdout) <= 0:
            LOG.info("the process (%s) is not running!" % self.process_name)
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
