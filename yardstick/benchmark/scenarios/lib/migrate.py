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

from yardstick.common.utils import Timer, IterableEvent
from yardstick.benchmark.scenarios import base

try:
    import ping
except ImportError:
    # temp fix for ping module import error on Python3
    # we need to replace the ping module anyway
    import mock
    ping = mock.MagicMock()

LOG = logging.getLogger(__name__)

TIMEOUT = 0.05
PACKAGE_SIZE = 64


class Migrate(base.OpenstackScenario):       # pragma: no cover
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "Migrate"
    LOGGER = LOG

    @staticmethod
    def _do_migrate(server_id, target_host):
        LOG.info('Start to migrate')
        cmd = ['nova', 'live-migration', server_id, target_host]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p.communicate()

    def __init__(self, scenario_cfg, context_cfg, default_server_id=None):
        if default_server_id is None:
            default_server_id = self.options.get('server', {}).get('id', '')
        super(Migrate, self).__init__(scenario_cfg, context_cfg, default_server_id)

    def _run(self, result):
        target_host = self.options.get('host')
        LOG.info('Target host is %s', target_host)

        with PingThread(self.server_ip, 'Instance') as ping_thread:
            try:
                self._do_migrate(self.server_id, target_host)
            except Exception as e:
                return [1, str(e).split('.')[0]]

            migrate_time = self._time_migration()
            LOG.info('Migration time is %s s', migrate_time)
            values = [0, migrate_time]

            current_host = self.host_name
            LOG.info('Current host is %s', current_host)
            if current_host.strip() != target_host.strip():
                LOG.error('current_host not equal to target_host')
                return [1, 'current_host not equal to target_host']

        try:
            downtime = ping_thread.delay
        except AttributeError:
            pass
        else:
            LOG.info('Downtime is %s s', downtime)
            values.append(downtime)

        return values

    def _time_migration(self):
        server = self.nova_client.servers.get(self.server_id)

        for _ in iter(server.status.lower, 'migrating'):
            pass

        LOG.debug('Instance status change to MIGRATING')
        with Timer() as timer:
            for status in iter(server.status.lower, 'active'):
                if status == 'error':
                    LOG.error('Instance status is ERROR')
                    raise RuntimeError('The instance status is error')

        LOG.debug('Instance status change to ACTIVE')
        return timer.get_delta_with_microseconds()


class PingThread(threading.Thread):     # pragma: no cover

    def __init__(self, target, name='Target'):
        super(PingThread, self).__init__()
        self.name = name
        self.target = target
        self.stop_exec = IterableEvent()
        self.timer = None
        LOG.info('%s IP is %s', self.name, self.target)

    @property
    def delay(self):
        return self.timer.delta

    @property
    def delay_with_microseconds(self):
        return self.timer.get_delta_with_microseconds()

    def __enter__(self):
        if not self.target:
            return
        self.ping_until_connected()
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_exec.set()

    def __iter__(self):
        return iter(self.ping_one, None)

    def ping_one(self):
        if not self.target:
            return
        return ping.do_one(self.target, TIMEOUT, PACKAGE_SIZE)

    def run(self):
        if not self.target:
            return
        LOG.debug('Start to ping %s %s', self.name.lower(), self.target)
        with Timer() as self.timer:
            for _ in zip(self.stop_exec, self):
                time.sleep(0.01)

    def ping_until_connected(self):
        for _ in self:
            pass
        LOG.info('%s %s is connected', self.name, self.target)
