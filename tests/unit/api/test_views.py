import unittest
import mock
import json

from api.views import Test


class TestTestCase(unittest.TestCase):

    @mock.patch('api.views.request')
    def test_post(self, mock_request):
        mock_request.json.get.side_effect = ['runTestSuite', {}]

        result = json.loads(Test().post())

        self.assertEqual('error', result['status'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
