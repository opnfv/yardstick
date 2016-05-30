##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from baseattacker import BaseAttacker
import yardstick.ssh as ssh
import yardstick.benchmark.scenarios.availability.util as util

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

        if "parameter" in self._config:
            parameter = self._config['parameter']
            str = util.buildshellparams(parameter)
            LOG.debug("parameter is: {0}".format(parameter))
            LOG.debug("parameter values are: {0}".format(parameter.values()))
            l = list(item for item in parameter.values())
            self.cmd_param = str.format(*l)

        self.fault_cfg = BaseAttacker.attacker_cfgs.get(self.key)
        self.inject_script = self.get_script_fullpath(
            self.fault_cfg['inject_script'])
        self.recovery_script = self.get_script_fullpath(
            self.fault_cfg['recovery_script'])

    def inject_fault(self):
        LOG.debug("{0} starting inject!".format(self.key))
        LOG.debug("the inject_script path:{0}".format(self.inject_script))

        if "parameter" in self._config:
            LOG.debug("the shell command is: {0}".format(self.cmd_param))
            exit_status, stdout, stderr = self.connection.execute(
                self.cmd_param,
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
        if "parameter" in self._config:
            LOG.debug("the shell command is: {0}".format(self.cmd_param))
            exit_status, stdout, stderr = self.connection.execute(
                self.cmd_param,
                stdin=open(self.recovery_script, "r"))
        else:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/bash -s ",
                stdin=open(self.recovery_script, "r"))

    # def buildshellparams(self,param):
    #    i = 0
    #    values = []
    #    result = '/bin/bash -s'
    #    for key in param.keys():
    #        values.append(param[key])
    #        result += " {%d}" % i
    #        i=i+1
    #    return result;
