##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from baseattacker import BaseAttacker
import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability import util

LOG = logging.getLogger(__name__)


class GeneralAttacker(BaseAttacker):

    __attacker_type__ = 'general-attacker'

    def setup(self):
        LOG.debug("config:%s context:%s" % (self._config, self._context))
        host = self._context.get(self._config['host'], None)
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")

        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        self.key = self._config['key']

        if "action_parameter" in self._config:
            actionParameter = self._config['action_parameter']
            str = util.buildshellparams(actionParameter)
            LOG.debug("inject parameter is: {0}".format(actionParameter))
            LOG.debug("inject parameter values are: {0}"
                      .format(actionParameter.values()))
            l = list(item for item in actionParameter.values())
            self.action_param = str.format(*l)

        if "rollback_parameter" in self._config:
            rollbackParameter = self._config['rollback_parameter']
            str = util.buildshellparams(rollbackParameter)
            LOG.debug("recover parameter is: {0}".format(rollbackParameter))
            LOG.debug("recover parameter values are: {0}".
                      format(rollbackParameter.values()))
            l = list(item for item in rollbackParameter.values())
            self.rollback_param = str.format(*l)

        self.fault_cfg = BaseAttacker.attacker_cfgs.get(self.key)
        self.inject_script = self.get_script_fullpath(
            self.fault_cfg['inject_script'])
        self.recovery_script = self.get_script_fullpath(
            self.fault_cfg['recovery_script'])

    def inject_fault(self):
        LOG.debug("{0} starting inject!".format(self.key))
        LOG.debug("the inject_script path:{0}".format(self.inject_script))

        if "action_parameter" in self._config:
            LOG.debug("the shell command is: {0}".format(self.action_param))
            exit_status, stdout, stderr = self.connection.execute(
                self.action_param,
                stdin=open(self.inject_script, "r"))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/bash -s ",
                stdin=open(self.inject_script, "r"))

        LOG.debug("the inject_fault's exit status is: {0}".format(exit_status))
        if exit_status == 0:
            LOG.debug("success,the inject_fault's output is: {0}"
                      .format(stdout))
        else:
            LOG.error(
                "the inject_fault's error, stdout:%s, stderr:%s" %
                (stdout, stderr))

    def recover(self):
        if "rollback_parameter" in self._config:
            LOG.debug("the shell command is: {0}".format(self.rollback_param))
            exit_status, stdout, stderr = self.connection.execute(
                self.rollback_param,
                stdin=open(self.recovery_script, "r"))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/bash -s ",
                stdin=open(self.recovery_script, "r"))
