##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from __future__ import print_function

import logging
import subprocess

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Bonnie(base.Scenario):
    """Execute bonnie benchmark in a host

    Parameters
    file_size - size fo the test file in MB. File size should be double RAM for good results.
        type:    int
        unit:    MB
        default: 2048
    ram_size - specify RAM size in MB to use, this is used to reduce testing time.
        type:    int
        unit:    MB
        default: na
    test_dir - this directory is where bonnie++ will create the benchmark operations.
        type:    string
        unit:    na
        default: "/tmp"
    test_user - the user who should perform the test. This is not required if you are not running
                as root.
        type:    string
        unit:    na
        default: na
    concurrency - number of thread to perform test
        type:    int
        unit:    na
        default: 1
    """
    __scenario_type__ = "Bonnie++"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        host = self.context_cfg["host"]

        self.client = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.client.wait(timeout=600)

        self.setup_done = True

    def run(self, result):    # pragma: no cover
        """execute the benchmark"""
        if not self.setup_done:
            self.setup()

        cmd_args = ""

        options = self.scenario_cfg["options"]
        file_size = options.get("file_size", 2048)
        test_dir = options.get("test_dir", "/tmp")

        if "ram_size" in options:
            cmd_args += " -r %s" % options["ram_size"]

        if "test_user" in options:
            cmd_args += " -u %s" % options["test_user"]

        if "concurrency" in options:
            cmd_args += " -c %s" % options["concurrency"]

        cmd = "bonnie++ -d %s -s %s %s" % (test_dir, file_size, cmd_args)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        raw_data = stdout.split('\n')[-2]
        result.update({"raw_data": raw_data})

        LOG.debug("Generating Bonnie++ HTML report...")
        with open("/tmp/bonnie.html", "w") as bon_file:
            p = subprocess.Popen(["bon_csv2html"], stdout=bon_file, stdin=subprocess.PIPE)
            p.communicate(raw_data)
        LOG.info('Bonnie++ benchmark completed, please find benchmark report at /tmp/bonnie.html')
