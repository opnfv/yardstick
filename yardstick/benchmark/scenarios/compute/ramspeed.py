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


class Ramspeed(base.Scenario):
    """Execute ramspeed benchmark in a host
    The ramspeed script takes a number of options which you can use to
    customise a test.  The full run time usage
    is:

    ramspeed -b ID [-g size] [-m size] [-l runs]

    -b  runs a specified benchmark (by an ID number):
        1 -- INTmark [writing]          4 -- FLOATmark [writing]
        2 -- INTmark [reading]          5 -- FLOATmark [reading]
        3 -- INTmem                     6 -- FLOATmem
    -g  specifies a # of Gbytes per pass (default is 8)
    -m  specifies a # of Mbytes per array (default is 32)
    -l  enables the BatchRun mode (for *mem benchmarks only),
       and specifies a # of runs (suggested is 5)
    -r  displays speeds in real megabytes per second (default: decimal)

    The -b option is required, others are recommended.

    Parameters
        type_id - specifies whether to run *mark benchmark or *mem benchmark
            type:       int
            unit:       n/a
            default:    n/a
        load - specifies a # of Gbytes per pass
            type:		int
            unit:		gigabyte
            default:	8
        block_size - specifies a # of Mbytes per array
            type:		int
            unit:		megabyte
            default:	32

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
        user = host.get("user", "ubuntu")
        ip = host.get("ip", None)
        key_filename = host.get('key_filename', "~/.ssh/id_rsa")

        LOG.info("user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client.run("cat > ~/ramspeed_mark_benchmark.sh",
                        stdin=open(self.mark_target_script, 'rb'))
        self.client.run("cat > ~/ramspeed_mem_benchmark.sh",
                        stdin=open(self.mem_target_script, 'rb'))
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
        else:
            raise RuntimeError("No such type_id: %s for Ramspeed scenario",
                               test_id)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            sla_min_bw = int(self.scenario_cfg['sla']['min_bandwidth'])
            for i in result["Result"]:
                bw = i["Bandwidth(MBps)"]
                if bw < sla_min_bw:
                    sla_error += "Bandwidth %f < " \
                        "sla:min_bandwidth(%f)" % (bw, sla_min_bw)
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
        'type_id': 1,
        'load': 16,
        'block_size': 64
    }

    sla = {
        'min_bandwidth': 6000,
        'action': 'monitor'
    }
    args = {'options': options, 'sla': sla}
    result = {}

    p = Ramspeed(args, ctx)
    p.run(result)
    print result

if __name__ == '__main__':
    _test()
