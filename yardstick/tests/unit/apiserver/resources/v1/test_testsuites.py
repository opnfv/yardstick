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


if __name__ == '__main__':
    unittest.main()
