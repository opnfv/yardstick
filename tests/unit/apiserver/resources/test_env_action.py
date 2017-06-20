##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import time
import unittest

from tests.unit.apiserver import APITestCase


class EnvTestCase(APITestCase):

    def test_create_grafana(self):
        if self.app is None:
            unittest.skip('host config error')
            return

        url = 'yardstick/env/action'
        data = {'action': 'create_grafana'}
        resp = self._post(url, data)

        time.sleep(0)

        task_id = resp['result']['task_id']
        url = '/yardstick/asynctask?task_id={}'.format(task_id)
        resp = self._get(url)

        time.sleep(0)

        self.assertTrue(u'status' in resp)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
