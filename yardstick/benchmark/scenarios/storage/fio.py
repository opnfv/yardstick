##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd.
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


class Fio(base.Scenario):
    """Execute fio benchmark in a host

  Parameters
    filename - file name for fio workload
        type:    string
        unit:    na
        default: /home/ubuntu/data.raw
    bs - block size used for the io units
        type:    int
        unit:    bytes
        default: 4k
    iodepth - number of iobuffers to keep in flight
        type:    int
        unit:    na
        default: 1
    rw - type of io pattern [read, write, randwrite, randread, rw, randrw]
        type:    string
        unit:    na
        default: write
    ramp_time - run time before logging any performance
        type:    int
        unit:    seconds
        default: 20

    Read link below for more fio args description:
        http://www.bluestop.org/fio/HOWTO.txt
    """
    __scenario_type__ = "Fio"

    TARGET_SCRIPT = "fio_benchmark.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.storage",
            Fio.TARGET_SCRIPT)
        host = self.context_cfg["host"]
        user = host.get("user", "root")
        ssh_port = host.get("ssh_port", ssh.DEFAULT_PORT)
        ip = host.get("ip", None)
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")

        LOG.info("user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename,
                              port=ssh_port)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/fio.sh",
                        stdin=open(self.target_script, "rb"))

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        default_args = "-ioengine=libaio -direct=1 -group_reporting " \
            "-numjobs=1 -time_based --output-format=json"

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg["options"]
        filename = options.get("filename", "/home/ubuntu/data.raw")
        bs = options.get("bs", "4k")
        iodepth = options.get("iodepth", "1")
        rw = options.get("rw", "write")
        ramp_time = options.get("ramp_time", 20)
        name = "yardstick-fio"
        # if run by a duration runner
        duration_time = self.scenario_cfg["runner"].get("duration", None) \
            if "runner" in self.scenario_cfg else None
        # if run by an arithmetic runner
        arithmetic_time = options.get("duration", None)
        if duration_time:
            runtime = duration_time
        elif arithmetic_time:
            runtime = arithmetic_time
        else:
            runtime = 30

        cmd_args = "-filename=%s -bs=%s -iodepth=%s -rw=%s -ramp_time=%s " \
                   "-runtime=%s -name=%s %s" \
                   % (filename, bs, iodepth, rw, ramp_time, runtime, name,
                      default_args)
        cmd = "sudo bash fio.sh %s %s" % (filename, cmd_args)
        LOG.debug("Executing command: %s", cmd)
        # Set timeout, so that the cmd execution does not exit incorrectly
        # when the test run time is last long
        timeout = int(ramp_time) + int(runtime) + 600
        status, stdout, stderr = self.client.execute(cmd, timeout=timeout)
        if status:
            raise RuntimeError(stderr)

        raw_data = json.loads(stdout)

        # The bandwidth unit is KB/s, and latency unit is us
        if rw in ["read", "randread", "rw", "randrw"]:
            result["read_bw"] = raw_data["jobs"][0]["read"]["bw"]
            result["read_iops"] = raw_data["jobs"][0]["read"]["iops"]
            result["read_lat"] = raw_data["jobs"][0]["read"]["lat"]["mean"]
        if rw in ["write", "randwrite", "rw", "randrw"]:
            result["write_bw"] = raw_data["jobs"][0]["write"]["bw"]
            result["write_iops"] = raw_data["jobs"][0]["write"]["iops"]
            result["write_lat"] = raw_data["jobs"][0]["write"]["lat"]["mean"]

        if "sla" in self.scenario_cfg:
            sla_error = ""
            for k, v in result.items():
                if k not in self.scenario_cfg['sla']:
                    continue

                if "lat" in k:
                    # For lattency small value is better
                    max_v = float(self.scenario_cfg['sla'][k])
                    if v > max_v:
                        sla_error += "%s %f > sla:%s(%f); " % (k, v, k, max_v)
                else:
                    # For bandwidth and iops big value is better
                    min_v = int(self.scenario_cfg['sla'][k])
                    if v < min_v:
                        sla_error += "%s %d < " \
                            "sla:%s(%d); " % (k, v, k, min_v)

            assert sla_error == "", sla_error


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename("yardstick.resources",
                                                   "files/yardstick_key")
    ctx = {
        "host": {
            "ip": "10.229.47.137",
            "user": "root",
            "key_filename": key_filename
        }
    }

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    options = {
        "filename": "/home/ubuntu/data.raw",
        "bs": "4k",
        "iodepth": "1",
        "rw": "rw",
        "ramp_time": 1,
        "duration": 10
    }
    result = {}
    args = {"options": options}

    fio = Fio(args, ctx)
    fio.run(result)
    print result

if __name__ == '__main__':
    _test()
