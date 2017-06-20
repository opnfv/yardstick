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


from yardstick.common import openstack_utils
from yardstick.common.utils import change_obj_to_dict
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)

TIMEOUT = 0.05
PACKAGE_SIZE = 64


try:
    import ping
except ImportError:
    # temp fix for ping module import error on Python3
    # we need to replace the ping module anyway
    import mock
    ping = mock.MagicMock()


class Migrate(base.Scenario):       # pragma: no cover
    """
    Execute a live migration for two hosts

    """

    __scenario_type__ = "Migrate"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.options = self.scenario_cfg.get('options', {})

        self.nova_client = openstack_utils.get_nova_client()

    def run(self, result):
        default_instance_id = self.options.get('server', {}).get('id', '')
        instance_id = self.options.get('server_id', default_instance_id)
        LOG.info('Instance id is %s', instance_id)

        target_host = self.options.get('host')
        LOG.info('Target host is %s', target_host)

        instance_ip = self.options.get('server_ip')
        if instance_ip:
            LOG.info('Instance ip is %s', instance_ip)

            self._ping_until_connected(instance_ip)
            LOG.info('Instance is connected')

            LOG.debug('Start to ping instance')
            ping_thread = self._do_ping_task(instance_ip)

        keys = self.scenario_cfg.get('output', '').split()
        try:
            LOG.info('Start to migrate')
            self._do_migrate(instance_id, target_host)
        except Exception as e:
            return self._push_to_outputs(keys, [1, str(e).split('.')[0]])
        else:
            migrate_time = self._get_migrate_time(instance_id)
            LOG.info('Migration time is %s s', migrate_time)

            current_host = self._get_current_host_name(instance_id)
            LOG.info('Current host is %s', current_host)
            if current_host.strip() != target_host.strip():
                LOG.error('current_host not equal to target_host')
                values = [1, 'current_host not equal to target_host']
                return self._push_to_outputs(keys, values)

        if instance_ip:
            ping_thread.flag = False
            ping_thread.join()

            downtime = ping_thread.get_delay()
            LOG.info('Downtime is %s s', downtime)

            values = [0, migrate_time, downtime]
            return self._push_to_outputs(keys, values)
        else:
            values = [0, migrate_time]
            return self._push_to_outputs(keys, values)

    def _do_migrate(self, server_id, target_host):

        cmd = ['nova', 'live-migration', server_id, target_host]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p.communicate()

    def _ping_until_connected(self, instance_ip):
        for i in range(3000):
            res = ping.do_one(instance_ip, TIMEOUT, PACKAGE_SIZE)
            if res:
                break

    def _do_ping_task(self, instance_ip):
        ping_thread = PingThread(instance_ip)
        ping_thread.start()
        return ping_thread

    def _get_current_host_name(self, server_id):

        return change_obj_to_dict(self.nova_client.servers.get(server_id))['OS-EXT-SRV-ATTR:host']

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


class PingThread(threading.Thread):     # pragma: no cover

    def __init__(self, target):
        super(PingThread, self).__init__()
        self.target = target
        self.flag = True
        self.delay = 0.0

    def run(self):
        count = 0
        while self.flag:
            res = ping.do_one(self.target, TIMEOUT, PACKAGE_SIZE)
            if not res:
                count += 1
            time.sleep(0.01)
        self.delay = (TIMEOUT + 0.01) * count

    def get_delay(self):
        return self.delay
