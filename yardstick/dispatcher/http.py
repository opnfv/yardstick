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
from datetime import datetime

from oslo_serialization import jsonutils
import requests
from requests import ConnectionError

from yardstick.dispatcher.base import Base as DispatchBase

LOG = logging.getLogger(__name__)


class HttpDispatcher(DispatchBase):
    """Dispatcher class for posting data into a http target.
    """

    __dispatcher_type__ = "Http"

    def __init__(self, task_id, conf):
        self.conf = conf.http
        super(HttpDispatcher, self).__init__(task_id)

    def setup(self):
        pass

    def teardown(self):
        pass

    def push(self, case, data):
        self._add_to_result(case, data)

    def flush(self):
        self._complete_result()
        self._push_result_data()

    def _push_result_data(self):
        if self.conf.target == '':
            # if the target was not set, do not do anything
            LOG.error('Dispatcher target was not set, no data will'
                      'be posted.')
            return

        testcases = self.result['result']['testcases']

        for case, data in testcases.items():
            self._upload_case_result(case, data)

    def _upload_case_result(self, case, data):
        try:
            scenario_data = data.get('tc_data', [])[0]
        except IndexError:
            current_time = datetime.now()
        else:
            timestamp = float(scenario_data.get('timestamp', 0.0))
            current_time = datetime.fromtimestamp(timestamp)

        info = self.result['result']['info']

        result = {
            "project_name": "yardstick",
            "case_name": case,
            "description": "yardstick ci scenario status",
            "scenario": info.get('deploy_scenario'),
            "version": info.get('version'),
            "pod_name": info.get('pod_name'),
            "installer": info.get('installer'),
            "build_tag": os.environ.get('BUILD_TAG'),
            "criteria": data.get('criteria'),
            "start_date": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "stop_date": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "trust_indicator": "",
            "details": ""
        }

        LOG.debug('Test result : %s', result)

        headers = {'Content-type': 'application/json'}
        try:
            res = requests.post(self.conf.target,
                                data=jsonutils.dump_as_bytes(result),
                                headers=headers,
                                timeout=int(self.conf.timeout))
        except ConnectionError as err:
            LOG.exception('Failed to record result data: %s', err)
        else:
            print(res.text)
            LOG.debug('Test result posting finished with status code'
                      ' %d.' % res.status_code)
