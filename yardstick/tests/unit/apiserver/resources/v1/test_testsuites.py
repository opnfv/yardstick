##############################################################################
# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import mock

import unittest

from yardstick.tests.unit.apiserver import APITestCase
from api.utils.thread import TaskThread


class TestsuiteTestCase(APITestCase):

    def test_run_test_suite(self):
        if self.app is None:
            unittest.skip('host config error')
            return

        TaskThread.start = mock.MagicMock()

        url = 'yardstick/testsuites/action'
        data = {
            'action': 'run_test_suite',
            'args': {
                'opts': {},
                'testsuite': 'opnfv_smoke'
            }
        }
        resp = self._post(url, data)
        self.assertEqual(resp.get('status'), 1)
