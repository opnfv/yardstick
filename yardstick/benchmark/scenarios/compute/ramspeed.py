##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import logging

import pkg_resources
from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.common import utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Ramspeed(base.Scenario):
    """Execute ramspeed benchmark in a host
    The ramspeed script takes a number of options which you can use to
    customise a test.  The full run time usage
    is:

    ramspeed -b ID [-g size] [-m size] [-l runs] [-r speed-format]

    -b  runs a specified benchmark (by an ID number):
       1 -- INTmark [writing]          4 -- FLOATmark [writing]
       2 -- INTmark [reading]          5 -- FLOATmark [reading]
       3 -- INTmem                     6 -- FLOATmem
       7 -- MMXmark [writing]          10 -- SSEmark [writing]
       8 -- MMXmark [reading]          11 -- SSEmark [reading]
       9 -- MMXmem                     12 -- SSEmem
       13 -- MMXmark (nt) [writing]    16 -- SSEmark (nt) [writing]
       14 -- MMXmark (nt) [reading]    17 -- SSEmark (nt) [reading]
       15 -- MMXmem (nt)               18 -- SSEmem (nt)
    In this scenario, only the first 6 test type will be used for testing.

    -g  specifies a # of Gbytes per pass (default is 8)
    -m  specifies a # of Mbytes per array (default is 32)
    -l  enables the BatchRun mode (for *mem benchmarks only),
       and specifies a # of runs (suggested is 5)
    -r  displays speeds in real megabytes per second (default: decimal)

    The -b option is required, others are recommended.

    Parameters
        type_id - specifies whether to run *mark benchmark or *mem benchmark
                  the type_id can be any number from 1 to 19
            type:       int
            unit:       n/a
            default:    1
        load - specifies a # of Gbytes per pass
            type:       int
            unit:       gigabyte
            default:    8
        block_size - specifies a # of Mbytes per array
            type:       int
            unit:       megabyte
            default:    32

    Parameters for *mem benchmark
        iteration - specifies a # of runs for each test
            type:       int
            unit:       n/a
            default:    1
    more info http://alasir.com/software/ramspeed
    """
    __scenario_type__ = "Ramspeed"

    RAMSPEED_MARK_SCRIPT = "ramspeed_mark_benchmark.bash"
    RAMSPEED_MEM_SCRIPT = "ramspeed_mem_benchmark.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.mark_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Ramspeed.RAMSPEED_MARK_SCRIPT)
        self.mem_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.compute",
            Ramspeed.RAMSPEED_MEM_SCRIPT)

        host = self.context_cfg["host"]

        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client._put_file_shell(
            self.mark_target_script, '~/ramspeed_mark_benchmark.sh')
        self.client._put_file_shell(
            self.mem_target_script, '~/ramspeed_mem_benchmark.sh')
        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        test_id = options.get('type_id', 1)
        load = options.get('load', 8)
        block_size = options.get('block_size', 32)

        if test_id == 3 or test_id == 6:
            iteration = options.get('iteration', 1)
            cmd = "sudo bash ramspeed_mem_benchmark.sh %d %d %d %d" % \
                  (test_id, load, block_size, iteration)
        elif 0 < test_id <= 5:
            cmd = "sudo bash ramspeed_mark_benchmark.sh %d %d %d" % \
                  (test_id, load, block_size)
        # only the test_id 1-6 will be used in this scenario
        else:
            raise RuntimeError("No such type_id: %s for Ramspeed scenario",
                               test_id)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        ramspeed_result = jsonutils.loads(stdout)
        result.update(utils.flatten_dict_key(ramspeed_result))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            sla_min_bw = int(self.scenario_cfg['sla']['min_bandwidth'])
            for i in ramspeed_result["Result"]:
                bw = i["Bandwidth(MBps)"]
                if bw < sla_min_bw:
                    sla_error += "Bandwidth %f < " \
                        "sla:min_bandwidth(%f)" % (bw, sla_min_bw)
            assert sla_error == "", sla_error
