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


from yardstick.benchmark.scenarios.availability.result_checker \
    .baseresultchecker import \
    BaseResultChecker
from yardstick.benchmark.scenarios.availability import Condition
import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.util import buildshellparams

LOG = logging.getLogger(__name__)


class GeneralResultChecker(BaseResultChecker):
    __result_checker__type__ = "general-result-checker"

    def setup(self):
        LOG.debug("config:%s context:%s", self._config, self._context)
        host = self._context.get(self._config['host'], None)

        self.connection = ssh.SSH.from_node(host, defaults={"user": "root"})
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        self.key = self._config['key']
        self.resultchecker_key = self._config['checker_key']
        self.type = self._config['checker_type']
        self.condition = self._config['condition']
        self.expectedResult = self._config['expectedValue']
        self.actualResult = object()

        self.key = self._config['key']
        if "parameter" in self._config:
            parameter = self._config['parameter']
            str = buildshellparams(parameter)
            l = list(item for item in parameter.values())
            self.shell_cmd = str.format(*l)

        self.resultchecker_cfgs = BaseResultChecker.resultchecker_cfgs.get(
            self.resultchecker_key)
        self.verify_script = self.get_script_fullpath(
            self.resultchecker_cfgs['verify_script'])

    def verify(self):
        if "parameter" in self._config:
            with open(self.verify_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    self.shell_cmd,
                    stdin=stdin_file)
            LOG.debug("action script of the operation is: %s",
                      self.verify_script)
            LOG.debug("action parameter the of operation is: %s",
                      self.shell_cmd)
        else:
            with open(self.verify_script, "r") as stdin_file:
                exit_status, stdout, stderr = self.connection.execute(
                    "/bin/bash -s ",
                    stdin=stdin_file)
            LOG.debug("action script of the operation is: %s",
                      self.verify_script)

        LOG.debug("exit_status ,stdout : %s ,%s", exit_status, stdout)
        if exit_status == 0 and stdout:
            self.actualResult = stdout
            LOG.debug("verifying resultchecker: %s", self.key)
            LOG.debug("verifying resultchecker,expected: %s",
                      self.expectedResult)
            LOG.debug("verifying resultchecker,actual: %s", self.actualResult)
            LOG.debug("verifying resultchecker,condition: %s", self.condition)
            if (type(self.expectedResult) is int):
                self.actualResult = int(self.actualResult)
            if self.condition == Condition.EQUAL:
                self.success = self.actualResult == self.expectedResult
            elif self.condition == Condition.GREATERTHAN:
                self.success = self.actualResult > self.expectedResult
            elif self.condition == Condition.GREATERTHANEQUAL:
                self.success = self.actualResult >= self.expectedResult
            elif self.condition == Condition.LESSTHANEQUAL:
                self.success = self.actualResult <= self.expectedResult
            elif self.condition == Condition.LESSTHAN:
                self.success = self.actualResult < self.expectedResult
            elif self.condition == Condition.IN:
                self.success = self.expectedResult in self.actualResult
            else:
                self.success = False
                LOG.debug(
                    "error happened when resultchecker: %s Invalid condition",
                    self.key)
        else:
            self.success = False
            LOG.debug(
                "error happened when resultchecker: %s verifying the result",
                self.key)
            LOG.error(stderr)

        LOG.debug(
            "verifying resultchecker: %s,the result is : %s", self.key,
            self.success)
        return self.success
