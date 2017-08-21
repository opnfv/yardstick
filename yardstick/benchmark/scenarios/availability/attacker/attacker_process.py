##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.attacker.baseattacker import \
    BaseAttacker

LOG = logging.getLogger(__name__)


class ProcessAttacker(BaseAttacker):

    __attacker_type__ = 'kill-process'

    def setup(self):
        LOG.debug("config:%s context:%s", self._config, self._context)
        host = self._context.get(self._config['host'], None)

        self.connection = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        self.service_name = self._config['process_name']
        self.fault_cfg = BaseAttacker.attacker_cfgs.get('kill-process')

        self.check_script = self.get_script_fullpath(
            self.fault_cfg['check_script'])
        self.inject_script = self.get_script_fullpath(
            self.fault_cfg['inject_script'])
        self.recovery_script = self.get_script_fullpath(
            self.fault_cfg['recovery_script'])

        self.data[self.service_name] = self.check()

    def check(self):
        with open(self.check_script, "r") as stdin_file:
            exit_status, stdout, stderr = self.connection.execute(
                "sudo /bin/sh -s {0}".format(self.service_name),
                stdin=stdin_file)

        if stdout:
            LOG.info("check the environment success!")
            return int(stdout.strip('\n'))
        else:
            LOG.error(
                "the host environment is error, stdout:%s, stderr:%s",
                stdout, stderr)
        return False

    def inject_fault(self):
        with open(self.inject_script, "r") as stdin_file:
            exit_status, stdout, stderr = self.connection.execute(
                "sudo /bin/sh -s {0}".format(self.service_name),
                stdin=stdin_file)

    def recover(self):
        with open(self.recovery_script, "r") as stdin_file:
            exit_status, stdout, stderr = self.connection.execute(
                "sudo /bin/bash -s {0} ".format(self.service_name),
                stdin=stdin_file)
        if exit_status:
            LOG.info("Fail to restart service!")
