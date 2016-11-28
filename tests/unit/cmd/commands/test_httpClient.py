import unittest
import mock
import json

from yardstick.common import httpClient


class HttpClientTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.httpClient.requests')
    def test_post(self, mock_requests):
        url = 'http://localhost:5000/hello'
        data = {'hello': 'world'}
        headers = {'Content-Type': 'application/json'}
        httpClient.HttpClient().post(url, data)
        mock_requests.post.assert_called_with(url, data=json.dumps(data),
                                              headers=headers)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
