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
    """Execute lmbench memory read latency or memory bandwidth benchmark in a host

    Parameters
        test_type - specifies whether to measure memory latency or bandwidth
            type:       string
            unit:       na
            default:    "latency"

    Parameters for memory read latency benchmark
        stride - number of locations in memory between starts of array elements
            type:       int
            unit:       bytes
            default:    128
        stop_size - maximum array size to test (minimum value is 0.000512)
            type:       int
            unit:       megabytes
            default:    16

        Results are accurate to the ~2-5 nanosecond range.

    Parameters for memory bandwidth benchmark
        size - the amount of memory to test
            type:       int
            unit:       kilobyte
            default:    128
        benchmark - the name of the memory bandwidth benchmark test to execute.
        Valid test names are rd, wr, rdwr, cp, frd, fwr, fcp, bzero, bcopy
            type:       string
            unit:       na
            default:    "rd"

    more info http://manpages.ubuntu.com/manpages/trusty/lmbench.8.html
    """
    __scenario_type__ = "Lmbench"

    LATENCY_BENCHMARK_SCRIPT = "lmbench_latency_benchmark.bash"
    BANDWIDTH_BENCHMARK_SCRIPT = "lmbench_bandwidth_benchmark.bash"

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.bandwidth_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Lmbench.BANDWIDTH_BENCHMARK_SCRIPT)
        self.latency_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Lmbench.LATENCY_BENCHMARK_SCRIPT)
        user = self.context.get("user", "ubuntu")
        host = self.context.get("host", None)
        key_filename = self.context.get('key_filename', "~/.ssh/id_rsa")

        LOG.info("user:%s, host:%s", user, host)
        self.client = ssh.SSH(user, host, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client.run("cat > ~/lmbench_latency.sh",
                        stdin=open(self.latency_target_script, 'rb'))
        self.client.run("cat > ~/lmbench_bandwidth.sh",
                        stdin=open(self.bandwidth_target_script, 'rb'))
        self.setup_done = True

    def run(self, args):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = args['options']
        test_type = options.get('test_type', 'latency')

        if test_type == 'latency':
            stride = options.get('stride', 128)
            stop_size = options.get('stop_size', 16)
            cmd = "sudo bash lmbench_latency.sh %d %d" % (stop_size, stride)
        elif test_type == 'bandwidth':
            size = options.get('size', 128)
            benchmark = options.get('benchmark', 'rd')
            warmup_repetitions = options.get('warmup', 0)
            cmd = "sudo bash lmbench_bandwidth.sh %d %s %d" % \
                  (size, benchmark, warmup_repetitions)
        else:
            raise RuntimeError("No such test_type: %s for Lmbench scenario",
                               test_type)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        data = json.loads(stdout)

        if "sla" in args:
            if test_type == 'latency':
                sla_max_latency = int(args['sla']['max_latency'])
                for result in data:
                    latency = result['latency']
                    assert latency <= sla_max_latency, "latency %f > " \
                        "sla:max_latency(%f)" % (latency, sla_max_latency)
            else:
                sla_min_bw = int(args['sla']['min_bandwidth'])
                bw = data["bandwidth(MBps)"]
                assert bw >= sla_min_bw, "bandwidth %f < " \
                    "sla:min_bandwidth(%f)" % (bw, sla_min_bw)

        return data


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

    p = Lmbench(ctx)

    options = {
        'test_type': 'latency',
        'stride': 128,
        'stop_size': 16
    }

    args = {'options': options}
    result = p.run(args)
    print result

if __name__ == '__main__':
    _test()
