##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from __future__ import print_function

import logging

import pkg_resources
from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Perf(base.Scenario):
    """Execute perf benchmark in a host

  Parameters
    events - perf tool software, hardware or tracepoint events
        type:       [str]
        unit:       na
        default:    ['task-clock']
    load - simulate load on the host by doing IO operations
        type:       bool
        unit:       na
        default:    false

    For more info about perf and perf events see https://perf.wiki.kernel.org
    """

    __scenario_type__ = "Perf"

    TARGET_SCRIPT = 'perf_benchmark.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.compute', Perf.TARGET_SCRIPT)
        host = self.context_cfg['host']

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(self.target_script, '~/perf_benchmark.sh')

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        events = options.get('events', ['task-clock'])

        events_string = ""
        for event in events:
            events_string += event + " "

        # if run by a duration runner
        duration_time = self.scenario_cfg["runner"].get("duration", None) \
            if "runner" in self.scenario_cfg else None
        # if run by an arithmetic runner
        arithmetic_time = options.get("duration", None)
        if duration_time:
            duration = duration_time
        elif arithmetic_time:
            duration = arithmetic_time
        else:
            duration = 30

        if 'load' in options:
            load = "dd if=/dev/urandom of=/dev/null"
        else:
            load = "sleep %d" % duration

        cmd = "sudo bash perf_benchmark.sh '%s' %d %s" \
            % (load, duration, events_string)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stdout)

        result.update(jsonutils.loads(stdout))

        if "sla" in self.scenario_cfg:
            metric = self.scenario_cfg['sla']['metric']
            exp_val = self.scenario_cfg['sla']['expected_value']
            smaller_than_exp = 'smaller_than_expected' \
                               in self.scenario_cfg['sla']

            if metric not in result:
                assert False, "Metric (%s) not found." % metric
            else:
                if smaller_than_exp:
                    assert result[metric] < exp_val, "%s %d >= %d (sla); " \
                        % (metric, result[metric], exp_val)
                else:
                    assert result[metric] >= exp_val, "%s %d < %d (sla); " \
                        % (metric, result[metric], exp_val)


def _test():
    """internal test function"""
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {
        'host': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename
        }
    }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    options = {'load': True}
    args = {'options': options}
    result = {}

    p = Perf(args, ctx)
    p.run(result)
    print(result)


if __name__ == '__main__':
    _test()
