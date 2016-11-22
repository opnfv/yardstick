import unittest
import mock
import json

from api.views import Test
from api.views import Result


class TestTestCase(unittest.TestCase):

    @mock.patch('api.views.request')
    def test_post(self, mock_request):
        mock_request.json.get.side_effect = ['hello', {}]

        result = json.loads(Test().post())

        self.assertEqual('error', result['status'])


class ResultTestCase(unittest.TestCase):

    @mock.patch('api.views.request')
    def test_get(self, mock_request):
        mock_request.args.get.return_value = 'hello'

        print Result().get()
        result = json.loads(Result().get())

        self.assertEqual('error', result['status'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
