##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
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
LOG.setLevel(logging.DEBUG)


class Cyclictest(base.Scenario):
    """Execute cyclictest benchmark on guest vm

  Parameters
    affinity - run thread #N on processor #N, if possible
        type:    int
        unit:    na
        default: 1
    interval - base interval of thread
        type:    int
        unit:    us
        default: 1000
    loops - number of loops, 0 for endless
        type:    int
        unit:    na
        default: 1000
    priority - priority of highest prio thread
        type:    int
        unit:    na
        default: 99
    threads - number of threads
        type:    int
        unit:    na
        default: 1
    histogram - dump a latency histogram to stdout after the run
                here set the max time to be tracked
        type:    int
        unit:    ms
        default: 90

    Read link below for more fio args description:
        https://rt.wiki.kernel.org/index.php/Cyclictest
    """
    __scenario_type__ = "Cyclictest"

    TARGET_SCRIPT = "cyclictest_benchmark.bash"

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Cyclictest.TARGET_SCRIPT)
        user = self.context.get("user", "root")
        host = self.context.get("host", None)
        key_filename = self.context.get("key_filename", "~/.ssh/id_rsa")

        LOG.debug("user:%s, host:%s", user, host)
        print "key_filename:" + key_filename
        self.client = ssh.SSH(user, host, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/cyclictest_benchmark.sh",
                        stdin=open(self.target_script, "rb"))

        self.setup_done = True

    def run(self, args, result):
        """execute the benchmark"""
        default_args = "-m -n -q"

        if not self.setup_done:
            self.setup()

        options = args["options"]
        affinity = options.get("affinity", 1)
        interval = options.get("interval", 1000)
        priority = options.get("priority", 99)
        loops = options.get("loops", 1000)
        threads = options.get("threads", 1)
        histogram = options.get("histogram", 90)

        cmd_args = "-a %s -i %s -p %s -l %s -t %s -h %s %s" \
                   % (affinity, interval, priority, loops,
                      threads, histogram, default_args)
        cmd = "sudo bash cyclictest_benchmark.sh %s" % (cmd_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))

        if "sla" in args:
            sla_error = ""
            for t, latency in result.items():
                if 'max_%s_latency' % t not in args['sla']:
                    continue

                sla_latency = int(args['sla']['max_%s_latency' % t])
                latency = int(latency)
                if latency > sla_latency:
                    sla_error += "%s latency %d > sla:max_%s_latency(%d); " % \
                        (t, latency, t, sla_latency)
            assert sla_error == "", sla_error


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename("yardstick.resources",
                                                   "files/yardstick_key")
    ctx = {
        "host": "192.168.50.28",
        "user": "root",
        "key_filename": key_filename
    }

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    cyclictest = Cyclictest(ctx)

    options = {
        "affinity": 2,
        "interval": 100,
        "priority": 88,
        "loops": 10000,
        "threads": 2,
        "histogram": 80
    }
    sla = {
        "max_min_latency": 100,
        "max_avg_latency": 500,
        "max_max_latency": 1000,
    }
    args = {
        "options": options,
        "sla": sla
    }

    result = cyclictest.run(args)
    print result

if __name__ == '__main__':
    _test()
