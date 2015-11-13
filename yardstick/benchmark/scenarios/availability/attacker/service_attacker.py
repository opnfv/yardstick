##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import logging

from attacker import BaseAttacker
import yardstick.ssh as ssh

LOG = logging.getLogger(__name__)


class ServiceAttacker(BaseAttacker):

    __attacker_type__ = 'stop-service'

    def _setup(self, config):
        LOG.debug("the attacker config:%s" % config)
        self.config = config
        host = config.get("host", None)
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")

        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        self.service_name = config['service_name']

        self.fault_cfg = config['fault_cfg']

        self.check_script = self.get_script_fullpath(self.fault_cfg['check_script'])
        self.inject_script = self.get_script_fullpath(self.fault_cfg['inject_script'])
        self.recovery_script = self.get_script_fullpath(self.fault_cfg['recovery_script'])

        if self._check():
            self.setup_done = True

    def _check(self):
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

    def _inject_fault(self):
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(self.service_name),
            stdin=open(self.inject_script, "r"))

    def _recovery(self):
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} ".format(self.service_name),
            stdin=open(self.recovery_script, "r"))

if __name__ == '__main__':

    LOG.debug('test logggingd')
    host = {
        "ip": "10.20.0.5",
        "user": "root",
        "key_filename": "/root/.ssh/id_rsa"
    }
    attack_cfg = {
       'service_name':'nova-api',
       'fault_type':'stop-service',
    }  

    attackers_cfg = []
    attackers_cfg.append(attack_cfg)

    config = {
        'attackers':attackers_cfg,
        'host':host  
    }
    
    fault_cfg = {
        'type': 'stop-service',
        'inject_script': 'scripts/stop_service.bash',
        'recovery_script': 'scripts/start_service.bash',
        'check_script': 'scripts/check_service.bash'
    }
    attacker_cfg = {
        'service_name': 'nova-api',
        'host': host,
        'fault_cfg': fault_cfg
    }
    p = ServiceAttacker(attacker_cfg)
    p.start()

    #attacker_instance = ttackerMgr()
    #attacker_instance.setup(config)
    #attacker_instance.do_attack()


