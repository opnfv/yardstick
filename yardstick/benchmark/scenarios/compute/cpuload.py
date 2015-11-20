##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""Processor statistics and system load."""

import pkg_resources
import logging
import time
import re
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios import base


LOG = logging.getLogger(__name__)


class CPULoad(base.Scenario):

    """Collect processor statistics and system load.

    This scenario reads system load averages and
    CPU usage statistics on a Linux host.

    CPU usage statistics are read using the utility 'mpstat'.

    If 'mpstat' is not installed on the host usage statistics
    are instead read directly from '/proc/stat'.

    Load averages are read from the file '/proc/loadavg'
    on the Linux host.

    Parameters
          interval - Time interval to measure CPU usage. A value of 0
                     indicates that processors statistics are to be
                     reported for the time since system startup (boot)

          type:       [int]
          unit:       seconds
          default:    0

    """

    __scenario_type__ = "CPUload"

    MPSTAT_FIELD_SIZE = 10

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction."""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.has_mpstat = False

    def setup(self):
        """Scenario setup."""
        host = self.context_cfg['host']
        user = host.get('user', 'ubuntu')
        ip = host.get('ip', None)
        key_filename = host.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename)
        self.client.wait(timeout=600)

        # Check if mpstat prog is installed
        status, _, _ = self.client.execute("mpstat -V &> /dev/null")
        if status != 0:
            LOG.info("MPSTAT is NOT installed")
            self.has_mpstat = False
        else:
            LOG.info("MPSTAT is installed")
            self.has_mpstat = True

        if 'options' in self.scenario_cfg:
            self.interval = self.scenario_cfg['options'].get("interval", 0)
        else:
            self.interval = 0

        self.setup_done = True

    def _execute_command(self, cmd):
        """Execute a command on server."""
        LOG.info("Executing: %s" % cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status != 0:
            raise RuntimeError("Failed executing command: ",
                               cmd, stderr)
        return stdout

    def _get_loadavg(self):
        """Get system load."""
        return {'loadavg': self._execute_command("cat /proc/loadavg").split()}

    def _get_cpu_usage_mpstat(self):
        """Get processor usage using mpstat."""
        if self.interval > 0:
            cmd = "sudo mpstat -P ON %s 1" % self.interval
        else:
            cmd = "sudo mpstat -P ON"

        result = self._execute_command(cmd)

        fields = []
        mpstat = {}

        time_marker = re.compile("^([0-9]+):([0-9]+):([0-9]+)$")
        ampm_marker = re.compile("(AM|PM)$")

        # Parse CPU stats
        for row in result.split('\n'):
            line = row.split()

            if line and re.match(time_marker, line[0]):

                if re.match(ampm_marker, line[1]):
                    del line[:2]
                else:
                    del line[:1]

                if line[0] == 'CPU':
                    # header fields
                    fields = line[1:]
                    if len(fields) != CPULoad.MPSTAT_FIELD_SIZE:
                        raise RuntimeError("mpstat: unexpected field size",
                                           fields)
                else:
                    # value fields
                    cpu = 'cpu' if line[0] == 'all' else 'cpu' + line[0]
                    values = line[1:]
                    if values and len(values) == len(fields):
                        mpstat[cpu] = dict(zip(fields, values))
                    else:
                        raise RuntimeError("mpstat: parse error", fields, line)

        return {'mpstat': mpstat}

    def _get_cpu_usage(self):
        """Get processor usage from /proc/stat."""
        fields = ['%usr', '%nice', '%sys', '%idle', '%iowait',
                  '%irq', '%soft', '%steal', '%guest', '%gnice']

        cmd = "grep '^cpu[0-9 ].' /proc/stat"

        if self.interval > 0:
            previous = self._execute_command(cmd).splitlines()
            time.sleep(self.interval)
            current = self._execute_command(cmd).splitlines()
        else:
            current = self._execute_command(cmd).splitlines()
            previous = current

        mpstat = {}

        for (prev, cur) in zip(previous, current):

            # Split string to list tokens
            cur_list = cur.split()
            prev_list = prev.split()

            cpu = cur_list[0]

            cur_stats = map(int, cur_list[1:])
            if self.interval > 0:
                prev_stats = map(int, prev_list[1:])
            else:
                prev_stats = [0] * len(cur_stats)

            # NB: Don't add 'guest' and 'gnice' as they
            # are already included in 'usr' and 'nice'.
            uptime_prev = sum(prev_stats[0:8])
            uptime_cur = sum(cur_stats[0:8])

            # Remove 'guest' and 'gnice' from 'usr' and 'nice'
            prev_stats[0] -= prev_stats[8]
            prev_stats[1] -= prev_stats[9]
            cur_stats[0] -= cur_stats[8]
            cur_stats[1] -= cur_stats[9]

            # number of samples (jiffies) in the interval
            samples = (uptime_cur - uptime_prev) or 1

            def _percent(x, y):
                if x < y:
                    return 0.0
                else:
                    return 100.0 * (x - y) / samples

            load = map(_percent, cur_stats, prev_stats)

            mpstat[cpu] = dict(zip(fields, load))

        return {'mpstat': mpstat}

    def run(self, result):
        """Read processor statistics."""
        if not self.setup_done:
            self.setup()

        result.update(self._get_loadavg())

        if self.has_mpstat:
            result.update(self._get_cpu_usage_mpstat())
        else:
            result.update(self._get_cpu_usage())

        # Note: No SLA as this scenario is only collecting statistics


def _test():
    """internal test function."""
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {
        'host': {
            'ip': '172.16.0.175',
            'user': 'ec2-user',
            'key_filename': key_filename
        }
    }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    args = {}
    result = {}

    p = CPULoad(args, ctx)
    p.run(result)
    import json
    print json.dumps(result)

if __name__ == '__main__':
    _test()
