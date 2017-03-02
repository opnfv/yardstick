##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""Memory load and statistics."""

from __future__ import absolute_import
import logging
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios import base
from six.moves import zip

LOG = logging.getLogger(__name__)


class MEMLoad(base.Scenario):
    """Collect memory statistics and system load.

    This scenario reads memory usage statistics on a Linux host.

    memory usage statistics are read using the utility 'free'.

    Parameters
        interval - Time interval to measure memory usage.
        Continuously display the result delay interval seconds apart.
        type:       [int]
        unit:       seconds
        default:    1

        count - specifies a # of measurments for each test
        type:       [int]
        unit:       N/A
        default:    1
    """
    __scenario_type__ = "MEMORYload"

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction."""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """Scenario setup."""
        host = self.context_cfg['host']

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        self.setup_done = True

    def _execute_command(self, cmd):
        """Execute a command on server."""
        LOG.info("Executing: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError("Failed executing command: ",
                               cmd, stderr)
        return stdout

    def _filtrate_result(self, result):
        fields = []
        free = {}
        ite = 0
        average = {'total': 0, 'used': 0, 'free': 0, 'buff/cache': 0,
                   'shared': 0}
        maximum = {'total': 0, 'used': 0, 'free': 0, 'buff/cache': 0,
                   'shared': 0}

        for row in result.split('\n'):
            line = row.split()

            if line and line[0] == 'total':
                # header fields
                fields = line[:]
            elif line and line[0] == 'Mem:':
                memory = 'memory' + str(ite)
                ite += 1
                values = line[1:]
                if values and len(values) == len(fields):
                    free[memory] = dict(list(zip(fields, values)))

        for entry in free:
            for item in average:
                average[item] += int(free[entry][item])

            for item in maximum:
                if int(free[entry][item]) > maximum[item]:
                    maximum[item] = int(free[entry][item])

        for item in average:
            average[item] = average[item] / len(free)

        return {'free': free, 'average': average, 'max': maximum}

    def _get_mem_usage(self):
        """Get memory usage using free."""
        options = self.scenario_cfg['options']
        interval = options.get("interval", 1)
        count = options.get("count", 1)

        cmd = "free -c '%s' -s '%s'" % (count, interval)

        result = self._execute_command(cmd)
        filtrated_result = self._filtrate_result(result)

        return filtrated_result

    def run(self, result):
        """Read processor statistics."""
        if not self.setup_done:
            self.setup()

        result.update(self._get_mem_usage())
