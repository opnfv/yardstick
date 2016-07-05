##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
from baseoperation import BaseOperation
import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.util import buildshellparams

LOG = logging.getLogger(__name__)


class GeneralOperaion(BaseOperation):

    __operation__type__ = "general-operation"

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
            str = buildshellparams(actionParameter)
            l = list(item for item in actionParameter.values())
            self.action_param = str.format(*l)

        if "rollback_parameter" in self._config:
            rollbackParameter = self._config['rollback_parameter']
            str = buildshellparams(rollbackParameter)
            l = list(item for item in rollbackParameter.values())
            self.rollback_param = str.format(*l)

        self.operation_cfgs = BaseOperation.operation_cfgs.get(self.key)
        self.action_script = self.get_script_fullpath(
            self.operation_cfgs['action_script'])
        self.rollback_script = self.get_script_fullpath(
            self.operation_cfgs['rollback_script'])

    def run(self):
        if "action_parameter" in self._config:
            exit_status, stdout, stderr = self.connection.execute(
                self.action_param,
                stdin=open(self.action_script, "r"))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/sh -s ",
                stdin=open(self.action_script, "r"))

        if exit_status == 0:
            LOG.debug("success,the operation's output is: {0}".format(stdout))
        else:
            LOG.error(
                "the operation's error, stdout:%s, stderr:%s" %
                (stdout, stderr))

    def rollback(self):
        if "rollback_parameter" in self._config:
            exit_status, stdout, stderr = self.connection.execute(
                self.rollback_param,
                stdin=open(self.rollback_script, "r"))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/sh -s ",
                stdin=open(self.rollback_script, "r"))
