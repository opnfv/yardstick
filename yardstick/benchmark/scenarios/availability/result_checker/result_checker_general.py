##############################################################################
# Copyright (c) 2016 Juan Qiu and others
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from baseresultchecker import BaseResultChecker
from yardstick.benchmark.scenarios.availability import Condition
import yardstick.ssh as ssh
from yardstick.benchmark.scenarios.availability.util import buildshellparams

LOG = logging.getLogger(__name__)


class GeneralResultChecker(BaseResultChecker):

    __result_checker__type__ = "general-result-checker"

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
            exit_status, stdout, stderr = self.connection.execute(
                self.shell_cmd,
                stdin=open(self.verify_script, "r"))
            LOG.debug("action script of the operation is: {0}"
                      .format(self.verify_script))
            LOG.debug("action parameter the of operation is: {0}"
                      .format(self.shell_cmd))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/bash -s ",
                stdin=open(self.verify_script, "r"))
            LOG.debug("action script of the operation is: {0}"
                      .format(self.verify_script))

        LOG.debug("exit_status ,stdout : {0} ,{1}".format(exit_status, stdout))
        if exit_status == 0 and stdout:
            self.actualResult = stdout
            LOG.debug("verifying resultchecker: {0}".format(self.key))
            LOG.debug("verifying resultchecker,expected: {0}"
                      .format(self.expectedResult))
            LOG.debug("verifying resultchecker,actual: {0}"
                      .format(self.actualResult))
            LOG.debug("verifying resultchecker,condition: {0}"
                      .format(self.condition))
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
                    "error happened when resultchecker: {0} Invalid condition"
                    .format(self.key))
        else:
            self.success = False
            LOG.debug(
                "error happened when resultchecker: {0} verifying the result"
                .format(self.key))
            LOG.error(stderr)

        LOG.debug(
            "verifying resultchecker: {0},the result is : {1}"
            .format(self.key, self.success))
        return self.success
