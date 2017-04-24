##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
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


class Unixbench(base.Scenario):
    """Execute Unixbench cpu benchmark in a host
    The Run script takes a number of options which you can use to customise a
    test, and you can specify the names of the tests to run.  The full usage
    is:

    Run [ -q | -v ] [-i <n> ] [-c <n> [-c <n> ...]] [test ...]

    -i <count>    Run <count> iterations for each test -- slower tests
                use <count> / 3, but at least 1.  Defaults to 10 (3 for
                slow tests).
    -c <n>        Run <n> copies of each test in parallel.

    Parameters for setting unixbench
        run_mode - Run in quiet mode or verbose mode
            type:       string
            unit:       None
            default:    None
        test_type - The available tests are organised into categories;
            type:       string
            unit:       None
            default:    None
        iterations - Run <count> iterations for each test -- slower tests
        use <count> / 3, but at least 1.  Defaults to 10 (3 for slow tests).
            type:       int
            unit:       None
            default:    None
        copies - Run <n> copies of each test in parallel.
            type:       int
            unit:       None
            default:    None

    more info https://github.com/kdlucas/byte-unixbench/blob/master/UnixBench
    """
    __scenario_type__ = "UnixBench"

    TARGET_SCRIPT = "unixbench_benchmark.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Unixbench.TARGET_SCRIPT)

        host = self.context_cfg["host"]

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client._put_file_shell(
            self.target_script, '~/unixbench_benchmark.sh')

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg["options"]

        run_mode = options.get("run_mode", None)
        LOG.debug("Executing run_mode: %s", run_mode)
        cmd_args = ""
        if run_mode == "quiet":
            cmd_args = "-q"
        elif run_mode == "verbose":
            cmd_args = "-v"

        option_pair_list = [("iterations", "-i"),
                            ("copies", "-c")]
        for option_pair in option_pair_list:
            if option_pair[0] in options:
                cmd_args += " %s %s " % (option_pair[1],
                                         options[option_pair[0]])

        test_type = options.get("test_type", None)
        if test_type is not None:
            cmd_args += " %s " % (test_type)

        cmd = "sudo bash unixbench_benchmark.sh %s" % (cmd_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            for t, score in result.items():
                if t not in self.scenario_cfg['sla']:
                    continue
                sla_score = float(self.scenario_cfg['sla'][t])
                score = float(score)
                if score < sla_score:
                    sla_error += "%s score %f < sla:%s_score(%f); " % \
                        (t, score, t, sla_score)
            assert sla_error == "", sla_error


def _test():  # pragma: no cover
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

    options = {
        'test_type': 'dhrystone',
        'run_mode': 'verbose'
    }

    args = {'options': options}
    result = {}

    p = Unixbench(args, ctx)
    p.run(result)
    print(result)


if __name__ == '__main__':
    _test()
