##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging
import yardstick.ssh as ssh

from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class CheckConnectivity(base.Scenario):
    """Check connectivity between two VMs"""

    __scenario_type__ = "CheckConnectivity"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg['options']

        try:
            self.source_ip_addr = self.options['src_ip_addr']
            self.dest_ip_addr = self.options['dest_ip_addr']
        except KeyError:
            host = self.context_cfg['host']
            target = self.context_cfg['target']
            self.ssh_user = host.get('user', 'ubuntu')
            self.ssh_port = host.get("ssh_port", 22)
            self.source_ip_addr = host.get('ip', None)
            self.dest_ip_addr = target.get('ipaddr', None)
            self.ssh_key = host.get('key_filename', '/root/.ssh/id_rsa')
            self.ssh_passwd = host.get('password', None)
            self.ssh_timeout = 600
        else:
            self.ssh_user = self.options.get("ssh_user", 'ubuntu')
            self.ssh_port = self.options.get("ssh_port", 22)
            self.ssh_key = self.options.get("ssh_key", '/root/.ssh/id_rsa')
            self.ssh_passwd = self.options.get("ssh_passwd", None)
            self.ssh_timeout = self.options.get("ssh_timeout", 600)

        self.connection = None
        self.setup_done = False

    def setup(self):
        """scenario setup"""

        if self.ssh_passwd is not None:
            LOG.info("Log in via pw, user:%s, host:%s, pw:%s",
                     self.ssh_user, self.source_ip_addr, self.ssh_passwd)
            self.connection = ssh.SSH(self.ssh_user,
                                      self.source_ip_addr,
                                      password=self.ssh_passwd,
                                      port=self.ssh_port)
        else:
            LOG.info("Log in via key, user:%s, host:%s, key_filename:%s",
                     self.ssh_user, self.source_ip_addr, self.ssh_key)
            self.connection = ssh.SSH(self.ssh_user,
                                      self.source_ip_addr,
                                      key_filename=self.ssh_key,
                                      port=self.ssh_port)

        self.connection.wait(timeout=self.ssh_timeout)
        self.setup_done = True

    def run(self, result):     # pragma: no cover
        """execute the test"""

        if not self.setup_done:
            self.setup()

        cmd = 'ping -c 4 ' + self.dest_ip_addr
        parameter = self.options.get('ping_parameter', None)
        if parameter:
            cmd += (" %s" % parameter)

        LOG.info("Executing command: %s", cmd)
        LOG.info("ping %s ==> %s", self.source_ip_addr, self.dest_ip_addr)
        status, stdout, stderr = self.connection.execute(cmd)

        conn_status = self.scenario_cfg['sla']['status']

        if bool(status) != bool(conn_status):
            LOG.info("%s ===> %s connectivity check passed!" % (self.source_ip_addr,
                                                                self.dest_ip_addr))
            result['Check_Connectivity'] = 'PASS'
        else:
            LOG.info("%s ===> %s connectivity check failed!" % (self.source_ip_addr,
                                                                self.dest_ip_addr))
            result['Check_Connectivity'] = 'FAIL'
