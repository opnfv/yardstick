##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
# bulk data test and req/rsp test are supported
import pkg_resources
import logging
import json

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Netperf(base.Scenario):
    """Execute netperf between two hosts

  Parameters
    testname - to specify the test you wish to perform.
    the valid testnames are TCP_STREAM, TCP_RR, UDP_STREAM, UDP_RR
        type:    string
        unit:    na
        default: TCP_STREAM
    send_msg_size - value set the local send size to value bytes.
        type:    int
        unit:    bytes
        default: na
    recv_msg_size - setting the receive size for the remote system.
        type:    int
        unit:    bytes
        default: na
    req_rsp_size - set the request and/or response sizes based on sizespec.
        type:    string
        unit:    na
        default: na
    duration - duration of the test
        type:    int
        unit:    seconds
        default: 20

    read link below for more netperf args description:
    http://www.netperf.org/netperf/training/Netperf.html
    """
    __scenario_type__ = "Netperf"

    TARGET_SCRIPT = 'netperf_benchmark.bash'

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Netperf.TARGET_SCRIPT)
        user = self.context.get('user', 'ubuntu')
        host = self.context.get('host', None)
        target = self.context.get('target', None)
        key_filename = self.context.get('key_filename', '~/.ssh/id_rsa')

        # netserver start automatically during the vm boot
        LOG.info("user:%s, target:%s", user, target)
        self.server = ssh.SSH(user, target, key_filename=key_filename)
        self.server.wait(timeout=600)

        LOG.info("user:%s, host:%s", user, host)
        self.client = ssh.SSH(user, host, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/netperf.sh",
                        stdin=open(self.target_script, "rb"))

        self.setup_done = True

    def run(self, args, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        # get global options
        ipaddr = args.get("ipaddr", '127.0.0.1')
        options = args['options']
        testname = options.get("testname", 'TCP_STREAM')
        duration_time = self.context.get("duration", None)
        arithmetic_time = options.get("duration", None)
        if duration_time:
            testlen = duration_time
        elif arithmetic_time:
            testlen = arithmetic_time
        else:
            testlen = 20

        cmd_args = "-H %s -l %s -t %s" % (ipaddr, testlen, testname)

        # get test specific options
        default_args = "-O 'THROUGHPUT,THROUGHPUT_UNITS,MEAN_LATENCY'"
        cmd_args += " -- %s" % default_args
        option_pair_list = [("send_msg_size", "-m"),
                            ("recv_msg_size", "-M"),
                            ("req_rsp_size", "-r")]
        for option_pair in option_pair_list:
            if option_pair[0] in options:
                cmd_args += " %s %s" % (option_pair[1],
                                        options[option_pair[0]])

        cmd = "sudo bash netperf.sh %s" % (cmd_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        result.update(json.loads(stdout))

        if result['mean_latency'] == '':
            raise RuntimeError(stdout)

        # sla check
        mean_latency = float(result['mean_latency'])
        if "sla" in args:
            sla_error = ""
            sla_max_mean_latency = int(args["sla"]["mean_latency"])

            if mean_latency > sla_max_mean_latency:
                sla_error += "mean_latency %f > sla_max_mean_latency(%f); " % \
                    (mean_latency, sla_max_mean_latency)
            assert sla_error == "", sla_error


def _test():
    '''internal test function'''
    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    runner_cfg = {}
    runner_cfg['type'] = 'Duration'
    runner_cfg['duration'] = 5
    runner_cfg['clinet'] = '10.0.2.33'
    runner_cfg['server'] = '10.0.2.53'
    runner_cfg['user'] = 'ubuntu'
    runner_cfg['output_filename'] = "/tmp/yardstick.out"
    runner_cfg['key_filename'] = key_filename

    scenario_args = {}
    scenario_args['options'] = {"testname": 'TCP_STREAM'}

    from yardstick.benchmark.runners import base as base_runner
    runner = base_runner.Runner.get(runner_cfg)
    runner.run("Netperf", scenario_args)
    runner.join()
    base_runner.Runner.release(runner)

if __name__ == '__main__':
    _test()
