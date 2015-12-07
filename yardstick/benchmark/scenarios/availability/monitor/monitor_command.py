##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import subprocess
import traceback

import basemonitor as basemonitor

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
        LOG.error("exec command '%s' error:\n " % command)
        LOG.error(traceback.format_exc())

    return exitcode, output


class MonitorOpenstackCmd(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "openstack-cmd"

    def monitor_func(self):
        cmd = self._config["command_name"]
        exit_status, stdout = _execute_shell_command(cmd)
        if exit_status:
            return False
        return True

    def verify_SLA(self):
        outage_time = self._result.get('outage_time', None)
        LOG.debug("the _result:%s" % self._result)
        max_outage_time = self._config["sla"]["max_outage_time"]
        if outage_time > max_outage_time:
            LOG.info("SLA failure: %f > %f" % (outage_time, max_outage_time))
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
        'monitor_type': 'openstack-cmd',
        'command_name': 'nova image-list',
        'monitor_time': 1,
        'SLA': {'max_outage_time': 5}
    }
    monitor_configs.append(config)

    p = basemonitor.MonitorMgr()
    p.init_monitors(monitor_configs, context)
    p.start_monitors()
    p.wait_monitors()
    p.verify()


if __name__ == '__main__':    # pragma: no cover
    _test()
