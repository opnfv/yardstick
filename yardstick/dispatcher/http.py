# Copyright 2013 IBM Corp
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this is a modified copy of
# ceilometer/ceilometer/dispatcher/http.py

from __future__ import absolute_import

import logging
import os

from oslo_serialization import jsonutils
import requests
from oslo_config import cfg

from yardstick.dispatcher.base import Base as DispatchBase

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
http_dispatcher_opts = [
    cfg.StrOpt('target',
               default='http://127.0.0.1:8000/results',
               help='The target where the http request will be sent. '
                    'If this is not set, no data will be posted. For '
                    'example: target = http://hostname:1234/path'),
    cfg.IntOpt('timeout',
               default=5,
               help='The max time in seconds to wait for a request to '
                    'timeout.'),
]

CONF.register_opts(http_dispatcher_opts, group="dispatcher_http")


class HttpDispatcher(DispatchBase):
    """Dispatcher class for posting data into a http target.
    """

    __dispatcher_type__ = "Http"

    def __init__(self, conf, config):
        super(HttpDispatcher, self).__init__(conf)
        self.headers = {'Content-type': 'application/json'}
        self.timeout = CONF.dispatcher_http.timeout
        self.target = CONF.dispatcher_http.target
        self.raw_result = []
        self.result = {
            "project_name": "yardstick",
            "description": "yardstick test cases result",
            "pod_name": os.environ.get('NODE_NAME', 'unknown'),
            "installer": os.environ.get('INSTALLER_TYPE', 'unknown'),
            "version": os.environ.get('YARDSTICK_VERSION', 'unknown')
        }

    def record_result_data(self, data):
        self.raw_result.append(data)

    def flush_result_data(self):
        if self.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will'
                      'be posted.')
            return

        self.result["details"] = self.raw_result

        case_name = ""
        for v in self.raw_result:
            if isinstance(v, dict) and "scenario_cfg" in v:
                case_name = v["scenario_cfg"]["tc"]
                break
        if case_name == "":
            LOG.error('Test result : %s',
                      jsonutils.dump_as_bytes(self.result))
            LOG.error('The case_name cannot be found, no data will be posted.')
            return

        self.result["case_name"] = case_name

        try:
            LOG.debug('Test result : %s',
                      jsonutils.dump_as_bytes(self.result))
            res = requests.post(self.target,
                                data=jsonutils.dump_as_bytes(self.result),
                                headers=self.headers,
                                timeout=self.timeout)
            LOG.debug('Test result posting finished with status code'
                      ' %d.' % res.status_code)
        except Exception as err:
            LOG.exception('Failed to record result data: %s',
                          err)
