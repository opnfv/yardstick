##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""cache hit/miss ratio and usage statistics"""

from __future__ import absolute_import
import pkg_resources
import logging
import re
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios import base
from six.moves import zip

LOG = logging.getLogger(__name__)


class CACHEstat(base.Scenario):
    """Collect cache statistics.

    This scenario reads system cache hit/miss ratio and other statistics on
    a Linux host.

    cache statistics are read using 'cachestat'.
    cachestat - show Linux page cache hit/miss statistics.
                Uses Linux ftrace.

    This is a proof of concept using Linux ftrace capabilities on older
    kernels, and works by using function profiling for in-kernel counters.
    Specifically, four kernel functions are traced:

    mark_page_accessed() for measuring cache accesses
    mark_buffer_dirty() for measuring cache writes
    add_to_page_cache_lru() for measuring page additions
    account_page_dirtied() for measuring page dirties

    It is possible that these functions have been renamed (or are different
    logically) for your kernel version, and this script will not work as-is.
    This script was written on Linux 3.13. This script is a sandcastle: the
    kernel may wash some away, and you'll need to rebuild.

    USAGE: cachestat [-Dht] [interval]
       eg,
         cachestat 5    # show stats every 5 seconds

    Run "cachestat -h" for full usage.

    WARNING: This uses dynamic tracing of kernel functions, and could cause
    kernel panics or freezes. Test, and know what you are doing, before use.
    It also traces cache activity, which can be frequent, and cost some
    overhead. The statistics should be treated as best-effort: there may be
    some error margin depending on unusual workload types.

    REQUIREMENTS: CONFIG_FUNCTION_PROFILER, awk.
    """
    __scenario_type__ = "CACHEstat"

    TARGET_SCRIPT = "cache_stat.bash"

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction."""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """Scenario setup."""
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            CACHEstat.TARGET_SCRIPT)

        host = self.context_cfg['host']

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client._put_file_shell(self.target_script, '~/cache_stat.sh')

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
        cachestat = {}
        data_marker = re.compile(r"\d+")
        ite = 0
        average = {'HITS': 0, 'MISSES': 0, 'DIRTIES': 0, 'RATIO': 0,
                   'BUFFERS_MB': 0, 'CACHE_MB': 0}
        maximum = {'HITS': 0, 'MISSES': 0, 'DIRTIES': 0, 'RATIO': 0,
                   'BUFFERS_MB': 0, 'CACHE_MB': 0}

        # Parse cache stats
        for row in result.split('\n'):
            line = row.split()

            if line and line[0] == 'HITS':
                # header fields
                fields = line[:]
            elif line and re.match(data_marker, line[0]):
                cache = 'cache' + str(ite)
                ite += 1
                values = line[:]
                if values and len(values) == len(fields):
                    cachestat[cache] = dict(list(zip(fields, values)))

        for entry in cachestat:
            for item in average:
                if item != 'RATIO':
                    average[item] += int(cachestat[entry][item])
                else:
                    average[item] += float(cachestat[entry][item][:-1])

            for item in maximum:
                if item != 'RATIO':
                    if int(cachestat[entry][item]) > maximum[item]:
                        maximum[item] = int(cachestat[entry][item])
                else:
                    if float(cachestat[entry][item][:-1]) > maximum[item]:
                        maximum[item] = float(cachestat[entry][item][:-1])

        for item in average:
            if item != 'RATIO':
                average[item] = average[item] / len(cachestat)
            else:
                average[item] = str(average[item] / len(cachestat)) + '%'

        return {'cachestat': cachestat, 'average': average, 'max': maximum}

    def _get_cache_usage(self):
        """Get cache statistics."""
        options = self.scenario_cfg['options']
        interval = options.get("interval", 1)

        cmd = "sudo bash cache_stat.sh %s" % (interval)

        result = self._execute_command(cmd)
        filtrated_result = self._filtrate_result(result)

        return filtrated_result

    def run(self, result):
        if not self.setup_done:
            self.setup()

        result.update(self._get_cache_usage())
