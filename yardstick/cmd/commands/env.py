##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import time

from yardstick.common.httpClient import HttpClient
from yardstick.common import constants as consts


class EnvCommand(object):
    '''

        Set of commands to prepare environment
    '''
    def do_influxdb(self, args):
        data = {'action': 'createInfluxDBContainer'}
        task_id = self._start_async_task(data)

        self._check_status(task_id)

    def do_grafana(self, args):
        data = {'action': 'createGrafanaContainer'}
        task_id = self._start_async_task(data)

        self._check_status(task_id)

    def do_prepare(self, args):
        data = {'action': 'prepareYardstickEnv'}
        task_id = self._start_async_task(data)

        self._check_status(task_id)

    def _start_async_task(self, data):
        url = consts.ENV_ACTION_API
        return HttpClient().post(url, data)['result']['task_id']

    def _check_status(self, task_id):
        url = '{}?task_id={}'.format(consts.ASYNC_TASK_API, task_id)

        status = 0
        while not status:
            time.sleep(5)
            response = HttpClient().get(url)
            status = response['status']

        switcher = {
            1: 'Finished',
            2: 'Error:{}'.format(response['result'])
        }
        print switcher[status]
