# ############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ############################################################################

from __future__ import print_function
from __future__ import absolute_import

import logging
import subprocess
import threading
import time
import pkg_resources

from datetime import datetime

from yardstick import ssh
from yardstick.common import openstack_utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Migrate(base.Scenario):
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "Migrate"

    PING = 'migrate_ping.bash'

    PRE_PATH = "yardstick.benchmark.scenarios.compute"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        host = self.context_cfg['host']
        self.user = host.get('user', 'ubuntu')
        self.port = host.get("ssh_port", ssh.DEFAULT_PORT)
        self.ip = host.get('ip')
        self.key_filename = host.get('key_filename', '/root/.ssh/id_rsa')
        self.password = host.get('password')

        self.nova_client = openstack_utils.get_nova_client()

    def _get_instance_client(self):

        if self.password is not None:
            LOG.info("Log in via pw, user:%s, host:%s, pw:%s",
                     self.user, self.ip, self.password)
            self.instance_client = ssh.SSH(self.user, self.ip,
                                           password=self.password,
                                           port=self.port)
        else:
            LOG.info("Log in via key, user:%s, host:%s, key_filename:%s",
                     self.user, self.ip, self.key_filename)
            self.instance_client = ssh.SSH(self.user, self.ip,
                                           key_filename=self.key_filename,
                                           port=self.port)

        self.instance_client.wait(timeout=600)

    def _do_ping_task(self):
        destination = self.context_cfg['target'].get('ip')

        self._get_instance_client()
        ping_script = pkg_resources.resource_filename(Migrate.PRE_PATH,
                                                      Migrate.PING)
        self.instance_client._put_file_shell(ping_script,
                                             '~/{}'.format(Migrate.PING))
        cmd = 'sudo bash {} {}'.format(Migrate.PING, destination)

        ping_thread = PingThread(self.instance_client.execute, cmd)
        ping_thread.start()
        return ping_thread

    def _get_current_host_name(self, server_id):

        key = 'OS-EXT-SRV-ATTR:host'
        cmd = "openstack server show %s | grep %s | awk '{print $4}'" % (
            server_id, key)

        LOG.debug('Executing cmd: %s', cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        current_host = p.communicate()[0].strip()

        LOG.debug('Host: %s', current_host)

        return current_host

    def run(self, result):
        target = self.scenario_cfg.get('target')

        migrate_time, interrupt_time = self._do_migrate(target)

        result.update({'migrate': migrate_time, 'interrupt': interrupt_time})

    def _do_migrate(self, target):
        ping_thread = self._do_ping_task()

        server = openstack_utils.get_server_by_name(target)

        current_host = self._get_current_host_name(server.id)

        host = self._get_migrate_host(current_host)
        LOG.debug('To be migrated: %s', host)

        start_time = datetime.now()
        cmd = ['nova', 'live-migration', server.id, host]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        LOG.debug('Migrated: %s', p.communicate()[0])

        while current_host.strip() != host.strip():
            current_host = self._get_current_host_name(server.id)
            time.sleep(0.1)

        end_time = datetime.now()
        migrate_time = (end_time - start_time).seconds
        print('live migration time is {}s'.format(migrate_time))

        ping_thread.join()

        interrupt_time = self._compute_interrupt_time(ping_thread.get_result())
        LOG.debug('The interrupt time is %s ms', interrupt_time)

        LOG.debug('First Job Done')

        return migrate_time, interrupt_time

    def _get_migrate_host(self, current_host):
        hosts = self.nova_client.hosts.list_all()
        compute_hosts = [a.host for a in hosts if a.service == 'compute']
        for host in compute_hosts:
            if host.strip() != current_host.strip():
                return host

    def _compute_interrupt_time(self, data):
        times = data[1][:-1].split('.')
        start = int(times[1])
        end = int(times[0])
        return (end - start) / 1000000


class PingThread(threading.Thread):

    def __init__(self, method, args):
        super(PingThread, self).__init__()
        self.method = method
        self.args = args
        self.result = None

    def run(self):
        self.result = self.method(self.args)

    def get_result(self):
        return self.result
