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
import time

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


class MonitorApi(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "openstack-api"

    def one_request(self):
        cmd = self._config["monitor_api"]
        exit_status, stdout = _execute_shell_command(cmd)
        return exit_status


def _test():    # pragma: no cover
    config = {
        'monitor_api': 'nova image-list',
        'monitor_type': 'openstack-api',
        'instance_count': 5
    }

    monitor_configs = []
    monitor_configs.append(config)

    p = basemonitor.MonitorMgr()
    p.setup(monitor_configs)
    p.do_monitor()
    time.sleep(5)
    p.stop_monitor()
    ret = p.get_result()
    print "the result:", ret


if __name__ == '__main__':    # pragma: no cover
    _test()
