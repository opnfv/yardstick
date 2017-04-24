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

from yardstick.benchmark.scenarios.availability.operation.baseoperation \
    import \
    BaseOperation

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.util import buildshellparams

LOG = logging.getLogger(__name__)


class GeneralOperaion(BaseOperation):

    __operation__type__ = "general-operation"

    def setup(self):
        LOG.debug("config:%s context:%s", self._config, self._context)
        host = self._context.get(self._config['host'], None)

        self.connection = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        self.key = self._config['key']
        self.operation_key = self._config['operation_key']

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

        self.operation_cfgs = BaseOperation.operation_cfgs.get(
            self.operation_key)
        self.action_script = self.get_script_fullpath(
            self.operation_cfgs['action_script'])
        self.rollback_script = self.get_script_fullpath(
            self.operation_cfgs['rollback_script'])

    def run(self):
        if "action_parameter" in self._config:
            with open(self.action_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    self.action_param,
                    stdin=stdin_file)
        else:
            with open(self.action_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "/bin/sh -s ",
                    stdin=stdin_file)

        if exit_status == 0:
            LOG.debug("success,the operation's output is: %s", stdout)
        else:
            LOG.error(
                "the operation's error, stdout:%s, stderr:%s",
                stdout, stderr)

    def rollback(self):
        if "rollback_parameter" in self._config:
            with open(self.rollback_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    self.rollback_param,
                    stdin=stdin_file)
        else:
            with open(self.rollback_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "/bin/sh -s ",
                    stdin=stdin_file)
