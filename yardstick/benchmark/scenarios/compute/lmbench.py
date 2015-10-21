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


class Lmbench(base.Scenario):
    """Execute lmbench memory read latency benchmark in a host

    Parameters
        stride - number of locations in memory between starts of array elements
            type:       int
            unit:       bytes
            default:    128
        stop_size - maximum array size to test (minimum value is 0.000512)
            type:       int
            unit:       megabytes
            default:    16

    Results are accurate to the ~2-5 nanosecond range.
    """
    __scenario_type__ = "Lmbench"

    TARGET_SCRIPT = "lmbench_benchmark.bash"

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Lmbench.TARGET_SCRIPT)
        host = self.context["host"]
        user = host.get("user", "ubuntu")
        ip = host.get("ip", None)
        key_filename = host.get('key_filename', "~/.ssh/id_rsa")

        LOG.info("user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/lmbench.sh",
                        stdin=open(self.target_script, 'rb'))

        self.setup_done = True

    def run(self, args):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = args['options']
        stride = options.get('stride', 128)
        stop_size = options.get('stop_size', 16)

        cmd = "sudo bash lmbench.sh %d %d" % (stop_size, stride)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        data = json.loads(stdout)

        if "sla" in args:
            sla_max_latency = int(args['sla']['max_latency'])
            for result in data:
                latency = result['latency']
                assert latency <= sla_max_latency, "latency %f > " \
                    "sla:max_latency(%f)" % (latency, sla_max_latency)

        return data


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

    p = Lmbench(ctx)

    options = {'stride': 128, 'stop_size': 16}

    args = {'options': options}
    result = p.run(args)
    print result

if __name__ == '__main__':
    _test()
