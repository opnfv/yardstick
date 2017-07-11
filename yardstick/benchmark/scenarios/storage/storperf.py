##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import os
import logging
import time

import requests
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class StorPerf(base.Scenario):
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
        super(StorPerf, self).__init__()
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg["options"]

        self.target = self.options.get("StorPerf_ip", None)
        self.query_interval = self.options.get("query_interval", 10)
        # Maximum allowed job time
        self.timeout = self.options.get('timeout', 3600)

        self.setup_done = False
        self.job_completed = False

    def _query_setup_state(self):
        """Query the stack status."""
        LOG.info("Querying the stack state...")
        setup_query = requests.get('http://%s:5000/api/v1.0/configurations'
                                   % self.target)

        setup_query_content = jsonutils.loads(
            setup_query.content)
        if setup_query_content["stack_created"]:
            self.setup_done = True
            LOG.debug("stack_created: %s",
                      setup_query_content["stack_created"])

    def setup(self):
        """Set the configuration."""
        env_args = {}
        env_args_payload_list = ["agent_count", "agent_flavor",
                                 "public_network", "agent_image",
                                 "volume_size"]

        for env_argument in env_args_payload_list:
            try:
                env_args[env_argument] = self.options[env_argument]
            except KeyError:
                pass

        LOG.info("Creating a stack on node %s with parameters %s",
                 self.target, env_args)
        setup_res = requests.post('http://%s:5000/api/v1.0/configurations'
                                  % self.target, json=env_args)

        setup_res_content = jsonutils.loads(
            setup_res.content)

        if setup_res.status_code != 200:
            raise RuntimeError("Failed to create a stack, error message:",
                               setup_res_content["message"])
        elif setup_res.status_code == 200:
            LOG.info("stack_id: %s", setup_res_content["stack_id"])

            while not self.setup_done:
                self._query_setup_state()
                time.sleep(self.query_interval)

    def _query_job_state(self, job_id):
        """Query the status of the supplied job_id and report on metrics"""
        LOG.info("Fetching report for %s...", job_id)
        report_res = requests.get('http://{}:5000/api/v1.0/jobs'.format
                                  (self.target),
                                  params={'id': job_id, 'type': 'status'})

        report_res_content = jsonutils.loads(
            report_res.content)

        if report_res.status_code != 200:
            raise RuntimeError("Failed to fetch report, error message:",
                               report_res_content["message"])
        else:
            job_status = report_res_content["Status"]

        LOG.debug("Job is: %s...", job_status)
        self.job_completed = job_status == "Completed"

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

        metadata = {"build_tag": "latest", "test_case": "opnfv_yardstick_tc074"}
        metadata_payload_dict = {"pod_name": "NODE_NAME",
                                 "scenario_name": "DEPLOY_SCENARIO",
                                 "version": "YARDSTICK_BRANCH"}

        for key, value in metadata_payload_dict.items():
            try:
                metadata[key] = os.environ[value]
            except KeyError:
                pass

        job_args = {"metadata": metadata}
        job_args_payload_list = ["block_sizes", "queue_depths", "deadline",
                                 "target", "nossd", "nowarm", "workload"]

        for job_argument in job_args_payload_list:
            try:
                job_args[job_argument] = self.options[job_argument]
            except KeyError:
                pass

        LOG.info("Starting a job with parameters %s", job_args)
        job_res = requests.post('http://%s:5000/api/v1.0/jobs' % self.target,
                                json=job_args)

        job_res_content = jsonutils.loads(job_res.content)

        if job_res.status_code != 200:
            raise RuntimeError("Failed to start a job, error message:",
                               job_res_content["message"])
        elif job_res.status_code == 200:
            job_id = job_res_content["job_id"]
            LOG.info("Started job id: %s...", job_id)

            while not self.job_completed:
                self._query_job_state(job_id)
                time.sleep(self.query_interval)

            terminate_res = requests.delete('http://%s:5000/api/v1.0/jobs' %
                                            self.target)

            if terminate_res.status_code != 200:
                terminate_res_content = jsonutils.loads(
                    terminate_res.content)
                raise RuntimeError("Failed to start a job, error message:",
                                   terminate_res_content["message"])

        # TODO: Support using ETA to polls for completion.
        #       Read ETA, next poll in 1/2 ETA time slot.
        #       If ETA is greater than the maximum allowed job time,
        #       then terminate job immediately.

        #   while not self.job_completed:
        #       esti_time = self._query_state(job_id)
        #       if esti_time > self.timeout:
        #           terminate_res = requests.delete('http://%s:5000/api/v1.0
        #                                           /jobs' % self.target)
        #       else:
        #           time.sleep(int(esti_time)/2)

            result_res = requests.get('http://%s:5000/api/v1.0/jobs?id=%s' %
                                      (self.target, job_id))
            result_res_content = jsonutils.loads(
                result_res.content)

            result.update(result_res_content)

    def teardown(self):
        """Deletes the agent configuration and the stack"""
        teardown_res = requests.delete('http://%s:5000/api/v1.0/\
                                       configurations' % self.target)

        if teardown_res.status_code == 400:
            teardown_res_content = jsonutils.loads(
                teardown_res.content)
            raise RuntimeError("Failed to reset environment, error message:",
                               teardown_res_content['message'])

        self.setup_done = False
