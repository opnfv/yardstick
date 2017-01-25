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
