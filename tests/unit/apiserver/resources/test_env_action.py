# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import time
import unittest

from tests.unit.apiserver import APITestCase


class EnvTestCase(APITestCase):

    def test_create_grafana(self):
        url = 'yardstick/env/action'
        data = {'action': 'createGrafanaContainer'}
        resp = self._post(url, data)

        time.sleep(1)

        task_id = resp['result']['task_id']
        url = '/yardstick/asynctask?task_id={}'.format(task_id)
        resp = self._get(url)

        time.sleep(2)

        self.assertTrue(u'status' in resp)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
