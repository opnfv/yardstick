##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import print_function
from __future__ import absolute_import

import logging

import pkg_resources
from oslo_serialization import jsonutils

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Nstat(base.Scenario):
    """Use nstat to monitor network metrics and measure IP datagram error rate
    and etc.
    """

    __scenario_type__ = "Nstat"

    NSTAT_SCRIPT = "nstat.bash"

    def __init__(self, scenario_cfg, context_cfg):
        """Scenario construction"""
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        """scenario setup"""
        self.nstat_target_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.networking",
            Nstat.NSTAT_SCRIPT)
        host = self.context_cfg["host"]
        user = host.get("user", "ubuntu")
        ssh_port = host.get("ssh_port", ssh.DEFAULT_PORT)
        ip = host.get("ip", None)
        key_filename = host.get('key_filename', "~/.ssh/id_rsa")

        LOG.info("user:%s, host:%s", user, ip)
        self.client = ssh.SSH(user, ip, key_filename=key_filename,
                              port=ssh_port)
        self.client.wait(timeout=600)

        # copy scripts to host
        self.client._put_file_shell(
            self.nstat_target_script, '~/nstat.sh')
        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()

        options = self.scenario_cfg['options']
        duration = options.get('duration', 60)

        cmd = "sudo bash nstat.sh %d" % (duration)

        LOG.debug("Executing command: %s", cmd)
        status, stdout, stderr = self.client.execute(cmd)

        if status:
            raise RuntimeError(stderr)

        result.update(jsonutils.loads(stdout))

        if "sla" in self.scenario_cfg:
            sla_error = ""
            for i, rate in result.items():
                if i not in self.scenario_cfg['sla']:
                    continue
                sla_rate = float(self.scenario_cfg['sla'][i])
                rate = float(rate)
                if rate > sla_rate:
                    sla_error += "%s rate %f > sla:%s_rate(%f); " % \
                        (i, rate, i, sla_rate)
            assert sla_error == "", sla_error
