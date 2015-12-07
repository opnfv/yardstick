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

LOG = logging.getLogger(__name__)


class ProcessAttacker(BaseAttacker):

    __attacker_type__ = 'kill-process'

    def setup(self):
        LOG.debug("config:%s context:%s" % (self._config, self._context))
        host = self._context.get(self._config['host'], None)
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")

        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
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

        if self.check():
            self.setup_done = True

    def check(self):
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(self.service_name),
            stdin=open(self.check_script, "r"))

        if stdout and "running" in stdout:
            LOG.info("check the envrioment success!")
            return True
        else:
            LOG.error(
                "the host envrioment is error, stdout:%s, stderr:%s" %
                (stdout, stderr))
        return False

    def inject_fault(self):
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(self.service_name),
            stdin=open(self.inject_script, "r"))

    def recover(self):
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} ".format(self.service_name),
            stdin=open(self.recovery_script, "r"))
