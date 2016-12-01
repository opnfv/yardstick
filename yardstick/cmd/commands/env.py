##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from yardstick.common.httpClient import HttpClient
from yardstick.common import constants


class EnvCommand(object):
    '''

        Set of commands to prepare environment
    '''
    def do_influxdb(self, args):
        url = constants.YARDSTICK_ENV_ACTION_API
        data = {'action': 'createInfluxDBContainer'}
        HttpClient().post(url, data)

    def do_grafana(self, args):
        url = constants.YARDSTICK_ENV_ACTION_API
        data = {'action': 'createGrafanaContainer'}
        HttpClient().post(url, data)

    def do_prepare(self, args):
        url = constants.YARDSTICK_ENV_ACTION_API
        data = {'action': 'prepareYardstickEnv'}
        HttpClient().post(url, data)
