##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import logging

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability import util
from yardstick.benchmark.scenarios.availability.attacker.baseattacker import \
    BaseAttacker

LOG = logging.getLogger(__name__)


class GeneralAttacker(BaseAttacker):

    __attacker_type__ = 'general-attacker'

    def setup(self):
        LOG.debug("config:%s context:%s", self._config, self._context)
        host = self._context.get(self._config['host'], None)

        self.connection = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        self.key = self._config['key']
        self.attack_key = self._config['attack_key']

        if "action_parameter" in self._config:
            actionParameter = self._config['action_parameter']
            str = util.buildshellparams(actionParameter)
            LOG.debug("inject parameter is: %s", actionParameter)
            LOG.debug("inject parameter values are: %s",
                      list(actionParameter.values()))
            l = list(actionParameter.values())
            self.action_param = str.format(*l)

        if "rollback_parameter" in self._config:
            rollbackParameter = self._config['rollback_parameter']
            str = util.buildshellparams(rollbackParameter)
            LOG.debug("recover parameter is: %s", rollbackParameter)
            LOG.debug("recover parameter values are: %s",
                      list(rollbackParameter.values()))
            l = list(rollbackParameter.values())
            self.rollback_param = str.format(*l)

        self.fault_cfg = BaseAttacker.attacker_cfgs.get(self.attack_key)
        self.inject_script = self.get_script_fullpath(
            self.fault_cfg['inject_script'])
        self.recovery_script = self.get_script_fullpath(
            self.fault_cfg['recovery_script'])

    def inject_fault(self):
        LOG.debug("%s starting inject!", self.key)
        LOG.debug("the inject_script path:%s", self.inject_script)

        if "action_parameter" in self._config:
            LOG.debug("the shell command is: %s", self.action_param)
            with open(self.inject_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "sudo {}".format(self.action_param),
                    stdin=stdin_file)
        else:
            with open(self.inject_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "sudo /bin/bash -s ",
                    stdin=stdin_file)

        LOG.debug("the inject_fault's exit status is: %s", exit_status)
        if exit_status == 0:
            LOG.debug("success,the inject_fault's output is: %s", stdout)
        else:
            LOG.error(
                "the inject_fault's error, stdout:%s, stderr:%s",
                stdout, stderr)

    def recover(self):
        if "rollback_parameter" in self._config:
            LOG.debug("the shell command is: %s", self.rollback_param)
            with open(self.recovery_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "sudo {}".format(self.rollback_param),
                    stdin=stdin_file)
        else:
            with open(self.recovery_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "sudo /bin/bash -s ",
                    stdin=stdin_file)
