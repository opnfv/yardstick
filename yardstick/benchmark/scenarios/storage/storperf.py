 ##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import json
import requests

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class StorPerf(base.scenario):
    """Execute StorPerf benchmark.
    Once the StorPerf container has been started and the ReST API exposed,
    you can interact directly with it using the ReST API. StorPerf comes with a
    Swagger interface that is accessible through the exposed port at:
    http://StorPerf:5000/swagger/index.html

  Command line options:
    target = [device or path] (Optional)
    The path to either an attached storage device (/dev/vdb, etc) or a
    directory path (/opt/storperf) that will be used to execute the performance
    test. In the case of a device, the entire device will be used.
    If not specified, the current directory will be used.

    workload = [workload module] (Optional)
    If not specified, the default is to run all workloads.
    The workload types are:
        rs: 100% Read, sequential data
        ws: 100% Write, sequential data
        rr: 100% Read, random access
        wr: 100% Write, random access
        rw: 70% Read / 30% write, random access

    nossd (Optional)
    Do not perform SSD style preconditioning.

    nowarm (Optional)
    Do not perform a warmup prior to measurements.

    report = [job_id] (Optional)
    Query the status of the supplied job_id and report on metrics.
    If a workload is supplied, will report on only that subset.

    For ReST API, the option is embedded in the URL as &option=.
    """
    __scenario_type__ = "StorPerf"

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction."""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """Set the configuration."""
        options = self.scenario_cfg['options']
        env_args = {}

        env_args_payload_list = ["agent_count", "agent_network", "volume_size"]

        for env_argument in env_args_payload_list:
            if env_argument in options:
                env_args[env_argument] = options[env_argument]

        setup_res = requests.post('http://StorPerf:5000/api/v1.0/configure',
                                  params=env_args)

        self.setup_done = True

    def run(self, result):
        """execute StorPerf benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        job_args = {}

        job_args_payload_list = ["target", "nossd", "nowarm", "workload"]

        for job_argument in job_args_payload_list:
            if job_argument in options:
                job_args[job_argument] = options[job_argument]

        job_res = requests.post('http://StorPerf:5000/api/v1.0/job',
                                params=job_args)

    def teardown(self):
        """Delete the stack and reset configration back to default"""
        teardown_res = requests.delete('http://StorPerf:5000/api/v1.0/configure')
