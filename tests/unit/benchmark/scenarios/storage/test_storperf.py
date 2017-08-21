#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.storage.storperf.StorPerf

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.storage import storperf


def mocked_requests_config_post(*args, **kwargs):
    class MockResponseConfigPost:

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigPost(
        '{"stack_id": "dac27db1-3502-4300-b301-91c64e6a1622",'
        '"stack_created": "false"}',
        200)


def mocked_requests_config_get(*args, **kwargs):
    class MockResponseConfigGet:

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigGet(
        '{"stack_id": "dac27db1-3502-4300-b301-91c64e6a1622",'
        '"stack_created": "true"}',
        200)


def mocked_requests_job_get(*args, **kwargs):
    class MockResponseJobGet:

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobGet(
        '{"Status": "Completed",\
         "_ssd_preconditioning.queue-depth.8.block-size.16384.duration": 6}',
        200)


def mocked_requests_job_post(*args, **kwargs):
    class MockResponseJobPost:

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobPost('{"job_id": \
                                 "d46bfb8c-36f4-4a40-813b-c4b4a437f728"}', 200)


def mocked_requests_job_delete(*args, **kwargs):
    class MockResponseJobDelete:

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobDelete('{}', 200)


def mocked_requests_delete(*args, **kwargs):
    class MockResponseDelete:

        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

    return MockResponseDelete('{}', 200)


def mocked_requests_delete_failed(*args, **kwargs):
    class MockResponseDeleteFailed:

        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

    if args[0] == "http://172.16.0.137:5000/api/v1.0/configurations":
        return MockResponseDeleteFailed('{"message": "Teardown failed"}', 400)

    return MockResponseDeleteFailed('{}', 404)


class StorPerfTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'cirros',
                'key_filename': "mykey.key"
            }
        }

        self.result = {}

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.post',
                side_effect=mocked_requests_config_post)
    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.get',
                side_effect=mocked_requests_config_get)
    def test_successful_setup(self, mock_post, mock_get):
        options = {
            "agent_count": 8,
            "public_network": 'ext-net',
            "volume_size": 10,
            "block_sizes": 4096,
            "queue_depths": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 0,
            "timeout": 60
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)

        s.setup()

        self.assertTrue(s.setup_done)

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.post',
                side_effect=mocked_requests_job_post)
    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.get',
                side_effect=mocked_requests_job_get)
    @mock.patch(
        'yardstick.benchmark.scenarios.storage.storperf.requests.delete',
        side_effect=mocked_requests_job_delete)
    def test_successful_run(self, mock_post, mock_get, mock_delete):
        options = {
            "agent_count": 8,
            "public_network": 'ext-net',
            "volume_size": 10,
            "block_sizes": 4096,
            "queue_depths": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 0,
            "timeout": 60
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)
        s.setup_done = True

        sample_output = '{"Status": "Completed",\
         "_ssd_preconditioning.queue-depth.8.block-size.16384.duration": 6}'

        expected_result = jsonutils.loads(sample_output)

        s.run(self.result)

        self.assertEqual(self.result, expected_result)

    @mock.patch(
        'yardstick.benchmark.scenarios.storage.storperf.requests.delete',
        side_effect=mocked_requests_delete)
    def test_successful_teardown(self, mock_delete):
        options = {
            "agent_count": 8,
            "public_network": 'ext-net',
            "volume_size": 10,
            "block_sizes": 4096,
            "queue_depths": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 60
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)

        s.teardown()

        self.assertFalse(s.setup_done)

    @mock.patch(
        'yardstick.benchmark.scenarios.storage.storperf.requests.delete',
        side_effect=mocked_requests_delete_failed)
    def test_failed_teardown(self, mock_delete):
        options = {
            "agent_count": 8,
            "public_network": 'ext-net',
            "volume_size": 10,
            "block_sizes": 4096,
            "queue_depths": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 60
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)

        self.assertRaises(AssertionError, s.teardown(), self.result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
