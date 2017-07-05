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
from yardstick.common import utils
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
            type:       float
            unit:       megabytes
            default:    16.0

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
        warmup - the number of repetitons to perform before taking measurements
            type:       int
            unit:       na
            default:    0
    more info http://manpages.ubuntu.com/manpages/trusty/lmbench.8.html
    """
    __scenario_type__ = "Lmbench"

    LATENCY_BENCHMARK_SCRIPT = "lmbench_latency_benchmark.bash"
    BANDWIDTH_BENCHMARK_SCRIPT = "lmbench_bandwidth_benchmark.bash"
    LATENCY_CACHE_SCRIPT = "lmbench_latency_for_cache.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.bandwidth_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Lmbench.BANDWIDTH_BENCHMARK_SCRIPT)
        self.latency_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Lmbench.LATENCY_BENCHMARK_SCRIPT)
        self.latency_for_cache_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Lmbench.LATENCY_CACHE_SCRIPT)
        host = self.context_cfg["host"]

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client._put_file_shell(
            self.latency_target_script, '~/lmbench_latency.sh')
        self.client._put_file_shell(
            self.bandwidth_target_script, '~/lmbench_bandwidth.sh')
        self.client._put_file_shell(
            self.latency_for_cache_script, '~/lmbench_latency_for_cache.sh')
        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        test_type = options.get('test_type', 'latency')

        if test_type == 'latency':
            stride = options.get('stride', 128)
            stop_size = options.get('stop_size', 16.0)
            cmd = "sudo bash lmbench_latency.sh %f %d" % (stop_size, stride)
        elif test_type == 'bandwidth':
            size = options.get('size', 128)
            benchmark = options.get('benchmark', 'rd')
            warmup_repetitions = options.get('warmup', 0)
            cmd = "sudo bash lmbench_bandwidth.sh %d %s %d" % \
                  (size, benchmark, warmup_repetitions)
        elif test_type == 'latency_for_cache':
            repetition = options.get('repetition', 1)
            warmup = options.get('warmup', 0)
            cmd = "sudo bash lmbench_latency_for_cache.sh %d %d" % \
                  (repetition, warmup)
        else:
            raise RuntimeError("No such test_type: %s for Lmbench scenario",
                               test_type)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        lmbench_result = {}
        if test_type == 'latency':
            lmbench_result.update(
                {"latencies": jsonutils.loads(stdout)})
        else:
            lmbench_result.update(jsonutils.loads(stdout))
        result.update(utils.flatten_dict_key(lmbench_result))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            if test_type == 'latency':
                sla_max_latency = int(self.scenario_cfg['sla']['max_latency'])
                for t_latency in lmbench_result["latencies"]:
                    latency = t_latency['latency']
                    if latency > sla_max_latency:
                        sla_error += "latency %f > sla:max_latency(%f); " \
                            % (latency, sla_max_latency)
            elif test_type == 'bandwidth':
                sla_min_bw = int(self.scenario_cfg['sla']['min_bandwidth'])
                bw = lmbench_result["bandwidth(MBps)"]
                if bw < sla_min_bw:
                    sla_error += "bandwidth %f < " \
                                 "sla:min_bandwidth(%f)" % (bw, sla_min_bw)
            elif test_type == 'latency_for_cache':
                sla_latency = float(self.scenario_cfg['sla']['max_latency'])
                cache_latency = float(lmbench_result['L1cache'])
                if sla_latency < cache_latency:
                    sla_error += "latency %f > sla:max_latency(%f); " \
                        % (cache_latency, sla_latency)
            assert sla_error == "", sla_error


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

    options = {
        'test_type': 'latency',
        'stride': 128,
        'stop_size': 16
    }

    sla = {'max_latency': 35, 'action': 'monitor'}
    args = {'options': options, 'sla': sla}
    result = {}

    p = Lmbench(args, ctx)
    p.run(result)
    print(result)


if __name__ == '__main__':
    _test()
