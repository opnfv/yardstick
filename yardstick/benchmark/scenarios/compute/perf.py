##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import logging
import json

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

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.compute', Perf.TARGET_SCRIPT)
        user = self.context.get('user', 'ubuntu')
        host = self.context.get('host', None)
        key_filename = self.context.get('key_filename', '~/.ssh/id_rsa')

        LOG.info("user:%s, host:%s", user, host)
        self.client = ssh.SSH(user, host, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/perf_benchmark.sh",
                        stdin=open(self.target_script, "rb"))

        self.setup_done = True

    def run(self, args, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = args['options']
        events = options.get('events', ['task-clock'])

        events_string = ""
        for event in events:
            events_string += event + " "

        # if run by a duration runner
        duration_time = self.context.get("duration", None)
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

        result.update(json.loads(stdout))

        if "sla" in args:
            sla_error = ""
            metric = args['sla']['metric']
            exp_val = args['sla']['expected_value']
            smaller_than_exp = 'smaller_than_expected' in args['sla']

            if metric not in result:
                sla_error += "Metric (%s) not found." % metric
            else:
                if smaller_than_exp:
                    if result[metric] >= exp_val:
                        sla_error += "%s %d >= %d (sla); " \
                            % (metric, result[metric], exp_val)
                else:
                    if result[metric] < exp_val:
                        sla_error += "%s %d < %d (sla); " \
                            % (metric, result[metric], exp_val)
            assert sla_error == "", sla_error


def _test():
    """internal test function"""
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {'host': '172.16.0.137',
           'user': 'ubuntu',
           'key_filename': key_filename
           }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    p = Perf(ctx)

    options = {'load': True}
    args = {'options': options}

    result = p.run(args)
    print result

if __name__ == '__main__':
    _test()
