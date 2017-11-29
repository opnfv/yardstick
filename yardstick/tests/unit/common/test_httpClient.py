##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.common import httpClient


class HttpClientTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.httpClient.requests')
    def test_post(self, mock_requests):
        url = 'http://localhost:5000/hello'
        data = {'hello': 'world'}
        headers = {'Content-Type': 'application/json'}
        httpClient.HttpClient().post(url, data)
        mock_requests.post.assert_called_with(
            url, data=jsonutils.dump_as_bytes(data),
            headers=headers)

    @mock.patch('yardstick.common.httpClient.requests')
    def test_get(self, mock_requests):
        url = 'http://localhost:5000/hello'
        httpClient.HttpClient().get(url)
        mock_requests.get.assert_called_with(url)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
