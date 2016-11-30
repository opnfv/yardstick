##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from yardstick.common.httpClient import HttpClient


class EnvCommand(object):

    def do_influxdb(self, args):
        url = 'http://localhost:5000/yardstick/env/action'
        data = {'action': 'createInfluxDBContainer'}
        HttpClient().post(url, data)
