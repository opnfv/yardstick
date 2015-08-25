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
LOG.setLevel(logging.DEBUG)


class Fio(base.Scenario):
    """Execute fio benchmark on host

  Parameters
    filename - file name for fio workload
        type:    string
        unit:    na
        default: /home/ec2-user/data.raw
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

    def __init__(self, context):
        self.context = context
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.storage",
            Fio.TARGET_SCRIPT)
        user = self.context.get("user", "root")
        host = self.context.get("host", None)
        key_filename = self.context.get("key_filename", "~/.ssh/id_rsa")

        LOG.debug("user:%s, host:%s", user, host)
        self.client = ssh.SSH(user, host, key_filename=key_filename)
        self.client.wait(timeout=600)

        # copy script to host
        self.client.run("cat > ~/fio.sh",
                        stdin=open(self.target_script, "rb"))

        self.setup_done = True

    def run(self, args):
        """execute the benchmark"""
        default_args = "-ioengine=libaio -direct=1 " \
            "-group_reporting -numjobs=1 -time_based"

        if not self.setup_done:
            self.setup()

        options = args["options"]
        filename = options.get("filename", "/home/ec2-user/data.raw")
        bs = options.get("bs", "4k")
        iodepth = options.get("iodepth", "1")
        rw = options.get("rw", "write")
        ramp_time = options.get("ramp_time", 20)
        name = "yardstick-fio"
        # if run by a duration runner
        duration_time = self.context.get("duration", None)
        # if run by an arithmetic runner
        arithmetic_time = options.get("duration", None)
        if duration_time:
            runtime = duration_time
        elif arithmetic_time:
            runtime = arithmetic_time
        else:
            runtime = 30

        args = "-filename=%s -bs=%s -iodepth=%s -rw=%s -ramp_time=%s " \
               "-runtime=%s -name=%s" \
               % (filename, bs, iodepth, rw, ramp_time, runtime, name)
        cmd = "sudo bash fio.sh %s %s %s" \
              % (filename, args, default_args)
        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        data = json.loads(stdout)

        # TODO: add sla check

        return data


def _test():
    '''internal test function'''
    key_filename = pkg_resources.resource_filename("yardstick.resources",
                                                   "files/yardstick_key")
    ctx = {
        "host": "10.0.0.101",
        "user": "ec2-user",
        "key_filename": key_filename
    }

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    fio = Fio(ctx)

    options = {
        "filename": "/home/ec2-user/data.raw",
        "bs": "4k",
        "iodepth": "1",
        "rw": "write",
        "ramp_time": 10,
    }
    args = {"options": options}

    result = fio.run(args)
    print result

if __name__ == '__main__':
    _test()
