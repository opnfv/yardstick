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
import time

# import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class StorPerf(base.scenario):
    """Execute StorPerf benchmark.
    Once the StorPerf container has been started and the ReST API exposed,
    you can interact directly with it using the ReST API. StorPerf comes with a
    Swagger interface that is accessible through the exposed port at:
    http://StorPerf:5000/swagger/index.html

  Command line options:
    target = [device or path] (Optional):
    The path to either an attached storage device (/dev/vdb, etc) or a
    directory path (/opt/storperf) that will be used to execute the performance
    test. In the case of a device, the entire device will be used.
    If not specified, the current directory will be used.

    workload = [workload module] (Optional):
    If not specified, the default is to run all workloads.
    The workload types are:
        rs: 100% Read, sequential data
        ws: 100% Write, sequential data
        rr: 100% Read, random access
        wr: 100% Write, random access
        rw: 70% Read / 30% write, random access

    nossd (Optional):
    Do not perform SSD style preconditioning.

    nowarm (Optional):
    Do not perform a warmup prior to measurements.

    report = [job_id] (Optional):
    Query the status of the supplied job_id and report on metrics.
    If a workload is supplied, will report on only that subset.

    """
    __scenario_type__ = "StorPerf"

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction."""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.target = self.options.get('StorPerf_ip', None)
        self.query_interval = self.options.get('query_interval', 10)
        # Maximum allowed job time
        # self.timeout = self.options.get('timeout', 3600)

        self.job_completed = False
        self.setup_done = False

    def setup(self):
        """Set the configuration."""
        env_args = {}
        env_args_payload_list = ["agent_count", "agent_network", "volume_size"]

        for env_argument in env_args_payload_list:
            if env_argument in self.options:
                env_args[env_argument] = self.options[env_argument]

        LOG.debug("Set the environment configration...")
        setup_res = requests.post('http://%s:5000/api/v1.0/\
                                  configurations' % self.target, json=env_args)

        if (setup_res.status_code == 400):
            setup_res_content = json.loads(setup_res.content)
            raise RuntimeError("Failed set up the environment, error message:",
                               setup_res_content['message'])

        self.setup_done = True

        """Due to a bug in StorPerf that prevents you from doing the setup and
        then going immediately to execute a run.
        https://jira.opnfv.org/browse/STORPERF-34
        """
        # Wait 2 minutes for StorPerf VMs are ready to accept SSH connection.
        time.sleep(120)

    def _query_state(self, job_id):
        """Query the status of the supplied job_id and report on metrics"""
        LOG.info("Fetching report for %s..." % (job_id,))
        report_res = requests.post('http://%s:5000/api/v1.0/jobs?id=%s' %
                                   (self.target, job_id,))

        if (report_res.status_code == 400):
            report_res_content = json.loads(report_res.content)
            raise RuntimeError("Failed fetch report, error message:",
                               report_res_content['message'])

        report_res_content = json.loads(report_res.content)
        job_status = report_res_content['status']

        LOG.info("Job is: %s..." % job_status)
        if job_status == "completed":
            self.job_completed = True

        # TODO: Support using StorPerf ReST API to read Job ETA.

        # if job_status == "completed":
        #     self.job_completed = True
        #     ETA = 0
        # elif job_status == "running":
        #     ETA = report_res_content['time']
        #
        # return ETA

    def run(self, result):
        """Execute StorPerf benchmark"""
        if not self.setup_done:
            self.setup()

        job_args = {}
        job_args_payload_list = ["target", "nossd", "nowarm", "workload"]

        for job_argument in job_args_payload_list:
            if job_argument in self.options:
                job_args[job_argument] = self.options[job_argument]

        LOG.debug("Calling start...")
        job_res = requests.post('http://%s:5000/api/v1.0/jobs' % self.target,
                                json=job_args)

        if (job_res.status_code == 400):
            job_res_content = json.loads(job_res.content)
            raise RuntimeError("Failed start a job, error message:",
                               job_res_content['message'])

        job_res_content = json.loads(job_res.content)
        job_id = job_res_content['job_id']
        LOG.info("Started job id: %s..." % job_id)

        while not self.job_completed:
            self._query_state(job_id)
            time.sleep(self.query_interval)

        # TODO: Support using ETA to polls for completion.
        # Read ETA, next poll in 1/2 ETA time slot.

        # while not self.job_completed:
        #     esti_time = self._query_state(job_id)
        #     if esti_time > self.timeout:
        #         terminate_res = requests.delete('http://%s:5000/api/v1.0
        #                                         /jobs' % self.target)
        #     else:
        #         time.sleep(int(est_time)/2)

        result_res = requests.post('http://%s:5000/api/v1.0/jobs?id=%s' %
                                   (self.target, job_id,))
        result_res_content = json.loads(result_res.content)
        job_result = result_res_content['workload']

        result.update(json.loads(job_result))

    def teardown(self):
        """Reset the environment configrations back to default"""
        teardown_res = requests.delete('http://%s:5000/api/v1.0/\
                                       configurations' % self.target)

        if (teardown_res.status_code == 400):
            teardown_res_content = json.loads(teardown_res.content)
            raise RuntimeError("Failed reset the environment, error message:",
                               teardown_res_content['message'])

        self.setup_done = False
