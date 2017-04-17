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

from datetime import datetime
import ping

import yardstick.ssh as ssh
from yardstick.common import openstack_utils
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Migrate(base.Scenario):
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "Migrate"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        self.nova_client = openstack_utils.get_nova_client()

        host = self.context_cfg['host']
        user = host.get('user', 'ubuntu')
        port = host.get("ssh_port", ssh.DEFAULT_PORT)
        ip = host.get('ip')
        key_filename = host.get('key_filename', '/root/.ssh/id_rsa')

        self.client = ssh.SSH(user, ip, key_filename=key_filename, port=port)
        self.client.wait(timeout=600)

    def _add_load(self):
        c, out, e = self.client.execute('free | grep Mem | awk "{print $2}"')
        total = int(out.split()[1])
        used = int(out.split()[2])
        count = abs(total * 0.5 - used) / 1024 / 128
        print("count is {}".format(count))
        if count != 0:
            self.client.execute('stress -t 10 -m {} --vm-keep'.format(count))

    def run(self, result):
        instance_name = self.scenario_cfg.get('host')
        instance_ip = self.context_cfg['host'].get('ip')
        LOG.debug('Instance name is %s', instance_name)
        LOG.debug('Instance ip is %s', instance_ip)

        self._ping_until_connected(instance_ip)
        LOG.info('Instance is connected')

        LOG.debug('Start to ping instance')
        ping_thread = self._do_ping_task(instance_ip)

        instance = openstack_utils.get_server_by_name(instance_name)

        current_host = self._get_current_host_name(instance.id)

        target_host = self._get_migrate_host(current_host)
        LOG.info('Current host is %s', current_host)

        self._add_load()

        LOG.info('Start to migrate')
        self._do_migrate(instance.id, target_host)

        migrate_time = self._get_migrate_time(instance.id)
        LOG.info('Migrations time is %s s', migrate_time)

        current_host = self._get_current_host_name(instance.id)
        LOG.info('Current host is %s', current_host)
        if current_host.strip() != target_host.strip():
            LOG.error('current_host not equal to target_host')

        ping_thread.flag = False
        ping_thread.join()

        downtime = ping_thread.get_delay()
        LOG.info('Downtime is %s s', downtime)

        result.update({'migration': migrate_time, 'downtime': downtime})

    def _do_migrate(self, server_id, target_host):

        cmd = ['nova', 'live-migration', server_id, target_host]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        LOG.debug('Migrated: %s', p.communicate()[0])

    def _ping_until_connected(self, instance_ip):
        for i in range(3000):
            res = ping.do_one(instance_ip, 0.05, 64)
            if res:
                break
        LOG.debug('Ping Connected')

    def _do_ping_task(self, instance_ip):
        ping_thread = PingThread(instance_ip)
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

    def _get_migrate_time(self, server_id):
        while True:
            status = self.nova_client.servers.get(server_id).status.lower()
            if status == 'migrating':
                start_time = datetime.now()
                break
        LOG.debug('Instance status change to MIGRATING')

        while True:
            status = self.nova_client.servers.get(server_id).status.lower()
            if status == 'active':
                end_time = datetime.now()
                break
            if status == 'error':
                LOG.error('Instance status is ERROR')
                raise RuntimeError('The instance status is error')
        LOG.debug('Instance status change to ACTIVE')

        duration = end_time - start_time
        return duration.seconds + duration.microseconds * 1.0 / 1e6

    def _get_migrate_host(self, current_host):
        hosts = self.nova_client.hosts.list_all()
        compute_hosts = [a.host for a in hosts if a.service == 'compute']
        for host in compute_hosts:
            if host.strip() != current_host.strip():
                return host


class PingThread(threading.Thread):

    def __init__(self, target):
        super(PingThread, self).__init__()
        self.target = target
        self.flag = True
        self.delay = 0.0

    def run(self):
        count = 0
        while self.flag:
            res = ping.do_one(self.target, 0.05, 64)
            if not res:
                count += 1
            time.sleep(0.05)
        self.delay = 0.06 * count

    def get_delay(self):
        return self.delay
