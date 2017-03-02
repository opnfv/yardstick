##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
# bulk data test and req/rsp test are supported
from __future__ import absolute_import
from __future__ import print_function

import logging

import pkg_resources
from oslo_serialization import jsonutils

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

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Netperf.TARGET_SCRIPT)
        host = self.context_cfg['host']
        target = self.context_cfg['target']

        # netserver start automatically during the vm boot
        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(target, defaults={"user": "ubuntu"})
        self.server.wait(timeout=600)

        LOG.info("user:%s, host:%s", host['user'], host['ip'])
        self.client = ssh.SSH.from_node(host, defaults={"user": "ubuntu"})
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(self.target_script, '~/netperf.sh')

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        # get global options
        ipaddr = self.context_cfg['target'].get("ipaddr", '127.0.0.1')
        options = self.scenario_cfg['options']
        testname = options.get("testname", 'TCP_STREAM')
        duration_time = self.scenario_cfg["runner"].get("duration", None) \
            if "runner" in self.scenario_cfg else None
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

        result.update(jsonutils.loads(stdout))

        if result['mean_latency'] == '':
            raise RuntimeError(stdout)

        # sla check
        mean_latency = float(result['mean_latency'])
        if "sla" in self.scenario_cfg:
            sla_max_mean_latency = int(
                self.scenario_cfg["sla"]["mean_latency"])

            assert mean_latency <= sla_max_mean_latency, \
                "mean_latency %f > sla_max_mean_latency(%f); " % \
                (mean_latency, sla_max_mean_latency)


def _test():
    """internal test function"""
    key_filename = pkg_resources.resource_filename("yardstick.resources",
                                                   "files/yardstick_key")
    ctx = {
        "host": {
            "ip": "10.229.47.137",
            "user": "root",
            "key_filename": key_filename
        },
        "target": {
            "ip": "10.229.47.137",
            "user": "root",
            "key_filename": key_filename,
            "ipaddr": "10.229.47.137"
        }
    }

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    options = {
        "testname": 'TCP_STREAM'
    }

    args = {"options": options}
    result = {}

    netperf = Netperf(args, ctx)
    netperf.run(result)
    print(result)


if __name__ == '__main__':
    _test()
