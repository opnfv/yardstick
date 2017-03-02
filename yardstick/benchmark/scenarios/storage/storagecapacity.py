##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and other.
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
from six.moves import range

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class StorageCapacity(base.Scenario):
    """Measure storage capacity and scale.

    Parameters:
        test_type - specified whether to measure.
        valid test type are disk_size, block_size, disk_utilization
            type: string
            unit: na
            default: "disk_size"
        interval - specified how ofter to stat disk utilization
            type: int
            unit: seconds
            default: 1
        count - specified how many times to stat disk utilization
            type: int
            unit: na
            default: 15

    This scenario reads hardware specification,
    disk size, block size and disk utilization.
    """
    __scenario_type__ = "StorageCapacity"
    TARGET_SCRIPT = "storagecapacity.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.storage",
            StorageCapacity.TARGET_SCRIPT)
        host = self.context_cfg['host']
        if host is None:
            raise RuntimeError('No right node.Please check the configuration')

        self.client = ssh.SSH.from_node(host, defaults={
            "user": "ubuntu", "password": "root"
        })
        self.client.wait(timeout=600)

        # copy script to host
        self.client._put_file_shell(self.target_script, '~/storagecapacity.sh')

        self.setup_done = True

    def _get_disk_utilization(self):
        """Get disk utilization using iostat."""
        options = self.scenario_cfg["options"]
        interval = options.get('interval', 1)
        count = options.get('count', 15)

        cmd = "sudo iostat -dx %d %d | awk 'NF==14 && \
               $1 !~ /Device/ {print $1,$14}'" % (interval, count)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)
        if status:
            raise RuntimeError(stderr)

        device_name_arr = []
        min_util_arr = []
        max_util_arr = []
        avg_util_arr = []
        for row in stdout.split('\n'):
            kv = row.split(' ')
            if len(kv) != 2:
                continue
            name = kv[0]
            util = float(kv[1])
            if name not in device_name_arr:
                device_name_arr.append(name)
                min_util_arr.append(util)
                max_util_arr.append(util)
                avg_util_arr.append(util)
            else:
                i = device_name_arr.index(name)
                min_util_arr[i] = min_util_arr[i] \
                    if min_util_arr[i] < util else util
                max_util_arr[i] = max_util_arr[i] \
                    if max_util_arr[i] > util else util
                avg_util_arr[i] += util
        r = {}
        for i in range(len(device_name_arr)):
            r[device_name_arr[i]] = {"min_util": min_util_arr[i],
                                     "max_util": max_util_arr[i],
                                     "avg_util": avg_util_arr[i] / count}
        return r

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg["options"]
        test_type = options.get('test_type', 'disk_size')

        if test_type == "disk_utilization":
            r = self._get_disk_utilization()
            result.update(r)
        else:
            cmd = "sudo bash storagecapacity.sh " + test_type

            LOG.debug("Executing command: %s", cmd)
            status, stdout, stderr = self.client.execute(cmd)
            if status:
                raise RuntimeError(stderr)

            result.update(jsonutils.loads(stdout))
