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

import json
import unittest

import mock
from oslo_serialization import jsonutils
import requests

from yardstick.benchmark.scenarios.storage import storperf


# pylint: disable=unused-argument
# disable this for now because I keep forgetting mock patch arg ordering
def mocked_requests_config_post(*args, **kwargs):
    class MockResponseConfigPost(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigPost(
        '{"stack_id": "dac27db1-3502-4300-b301-91c64e6a1622",'
        '"stack_created": false}',
        200)


def mocked_requests_config_post_fail(*args, **kwargs):
    class MockResponseConfigPost(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigPost(
        '{"message": "ERROR: Parameter \'public_network\' is invalid: ' +
        'Error validating value \'foo\': Unable to find network with ' +
        'name or id \'foo\'"}',
        400)


def mocked_requests_config_get(*args, **kwargs):
    class MockResponseConfigGet(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigGet(
        '{"stack_id": "dac27db1-3502-4300-b301-91c64e6a1622",'
        '"stack_created": true}',
        200)


def mocked_requests_config_get_not_created(*args, **kwargs):
    class MockResponseConfigGet(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigGet(
        '{"stack_id": "",'
        '"stack_created": false}',
        200)


def mocked_requests_config_get_no_payload(*args, **kwargs):
    class MockResponseConfigGet(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseConfigGet(
        '{}',
        200)


def mocked_requests_initialize_post_fail(*args, **kwargs):
    class MockResponseJobPost(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobPost(
        '{"message": "ERROR: Stack StorPerfAgentGroup does not exist"}',
        400)


def mocked_requests_job_get(*args, **kwargs):
    class MockResponseJobGet(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobGet(
        '{"Status": "Completed",\
         "_ssd_preconditioning.queue-depth.8.block-size.16384.duration": 6}',
        200)


def mocked_requests_job_post(*args, **kwargs):
    class MockResponseJobPost(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobPost('{"job_id": \
                                 "d46bfb8c-36f4-4a40-813b-c4b4a437f728"}', 200)


def mocked_requests_job_post_fail(*args, **kwargs):
    class MockResponseJobPost(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobPost(
        '{"message": "ERROR: Stack StorPerfAgentGroup does not exist"}',
        400)


def mocked_requests_job_delete(*args, **kwargs):
    class MockResponseJobDelete(object):

        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

    return MockResponseJobDelete('{}', 200)


def mocked_requests_delete(*args, **kwargs):
    class MockResponseDelete(object):

        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

    return MockResponseDelete('{}', 200)


def mocked_requests_delete_failed(*args, **kwargs):
    class MockResponseDeleteFailed(object):

        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

    return MockResponseDeleteFailed('{"message": "Teardown failed"}', 400)


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

    @mock.patch.object(requests, 'post')
    @mock.patch.object(requests, 'get')
    def test_setup(self, mock_get, mock_post):
        mock_post.side_effect = [mocked_requests_config_post(),
                                 mocked_requests_job_post()]
        mock_get.side_effect = [mocked_requests_config_get(),
                                mocked_requests_job_get()]

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

    @mock.patch.object(requests, 'get')
    def test_query_setup_state_unsuccessful(self, mock_get):
        mock_get.side_effect = mocked_requests_config_get_not_created
        args = {
            "options": {}
        }
        s = storperf.StorPerf(args, self.ctx)
        result = s._query_setup_state()
        self.assertFalse(result)

    @mock.patch.object(requests, 'get')
    def test_query_setup_state_no_payload(self, mock_get):
        mock_get.side_effect = mocked_requests_config_get_no_payload
        args = {
            "options": {}
        }
        s = storperf.StorPerf(args, self.ctx)
        result = s._query_setup_state()
        self.assertFalse(result)

    @mock.patch.object(requests, 'post')
    @mock.patch.object(requests, 'get')
    def test_setup_config_post_failed(self, mock_get, mock_post):
        mock_post.side_effect = mocked_requests_config_post_fail

        args = {
            "options": {
                "public_network": "foo"
            }
        }

        s = storperf.StorPerf(args, self.ctx)

        self.assertRaises(RuntimeError, s.setup)

    @mock.patch.object(requests, 'get')
    @mock.patch.object(requests, 'post')
    def test_run_v1_successful(self, mock_post, mock_get):
        mock_post.side_effect = mocked_requests_job_post
        mock_get.side_effect = mocked_requests_job_get

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
        expected_post = {
            'metadata': {
                'build_tag': 'latest',
                'test_case': 'opnfv_yardstick_tc074'
            },
            'deadline': 60,
            'block_sizes': 4096,
            'queue_depths': 4,
            "workload": "rs",
            'agent_count': 8
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

        mock_post.assert_called_once_with(
            'http://192.168.23.2:5000/api/v1.0/jobs',
            json=jsonutils.loads(json.dumps(expected_post)))

        self.assertEqual(self.result, expected_result)

    @mock.patch.object(requests, 'get')
    @mock.patch.object(requests, 'post')
    def test_run_v2_successful(self, mock_post, mock_get):
        mock_post.side_effect = mocked_requests_job_post
        mock_get.side_effect = mocked_requests_job_get

        options = {
            "agent_count": 8,
            "public_network": 'ext-net',
            "volume_size": 10,
            "block_sizes": 4096,
            "queue_depths": 4,
            "workloads": {
                "read_sequential": {
                    "rw": "rs"
                }
            },
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 0,
            "timeout": 60
        }
        expected_post = {
            'metadata': {
                'build_tag': 'latest',
                'test_case': 'opnfv_yardstick_tc074'
            },
            'deadline': 60,
            'block_sizes': 4096,
            'queue_depths': 4,
            'workloads': {
                'read_sequential': {
                    'rw': 'rs'
                }
            },
            'agent_count': 8
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
        mock_post.assert_called_once_with(
            'http://192.168.23.2:5000/api/v2.0/jobs',
            json=expected_post)

        self.assertEqual(self.result, expected_result)

    @mock.patch('time.sleep')
    @mock.patch.object(requests, 'get')
    @mock.patch.object(requests, 'post')
    def test_run_failed(self, mock_post, mock_get, _):
        mock_post.side_effect = mocked_requests_job_post_fail
        mock_get.side_effect = mocked_requests_job_get

        options = {
            "agent_count": 8,
            "public_network": 'ext-net',
            "volume_size": 10,
            "block_sizes": 4096,
            "queue_depths": 4,
            "workloads": {
                "read_sequential": {
                    "rw": "rs"
                }
            },
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 0,
            "timeout": 60
        }
        expected_post = {
            'metadata': {
                'build_tag': 'latest',
                'test_case': 'opnfv_yardstick_tc074'
            },
            'deadline': 60,
            'block_sizes': 4096,
            'queue_depths': 4,
            'workloads': {
                'read_sequential': {
                    'rw': 'rs'
                }
            },
            'agent_count': 8
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)
        s.setup_done = True

        self.assertRaises(RuntimeError, s.run, self.ctx)
        mock_post.assert_called_once_with(
            'http://192.168.23.2:5000/api/v2.0/jobs',
            json=expected_post)

    @mock.patch('time.sleep')
    @mock.patch.object(requests, 'get')
    @mock.patch.object(requests, 'post')
    @mock.patch.object(storperf.StorPerf, 'setup')
    def test_run_calls_setup(self, mock_setup, mock_post, mock_get, _):
        mock_post.side_effect = mocked_requests_job_post
        mock_get.side_effect = mocked_requests_job_get

        args = {
            "options": {
                'timeout': 60,
            }
        }

        s = storperf.StorPerf(args, self.ctx)

        s.run(self.result)

        mock_setup.assert_called_once()

    @mock.patch('time.sleep')
    @mock.patch.object(requests, 'get')
    @mock.patch.object(requests, 'post')
    def test_initialize_disks(self, mock_post, mock_get, _):
        mock_post.side_effect = mocked_requests_job_post
        mock_get.side_effect = mocked_requests_job_get

        args = {
            "options": {
                "StorPerf_ip": "192.168.23.2"
            }
        }

        s = storperf.StorPerf(args, self.ctx)

        s.initialize_disks()

        mock_post.assert_called_once_with(
            'http://192.168.23.2:5000/api/v1.0/initializations',
            json={})

    @mock.patch('time.sleep')
    @mock.patch.object(requests, 'get')
    @mock.patch.object(requests, 'post')
    def test_initialize_disks_post_failed(self, mock_post, mock_get, _):
        mock_post.side_effect = mocked_requests_initialize_post_fail
        mock_get.side_effect = mocked_requests_job_get

        args = {
            "options": {
                "StorPerf_ip": "192.168.23.2"
            }
        }

        s = storperf.StorPerf(args, self.ctx)

        self.assertRaises(RuntimeError, s.initialize_disks)
        mock_post.assert_called_once_with(
            'http://192.168.23.2:5000/api/v1.0/initializations',
            json={})

    @mock.patch.object(requests, 'delete')
    def test_teardown(self, mock_delete):
        mock_delete.side_effect = mocked_requests_job_delete
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
        mock_delete.assert_called_once_with(
            'http://192.168.23.2:5000/api/v1.0/configurations')

    @mock.patch.object(requests, 'delete')
    def test_teardown_request_delete_failed(self, mock_delete):
        mock_delete.side_effect = mocked_requests_delete_failed
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

        self.assertRaises(RuntimeError, s.teardown)
        mock_delete.assert_called_once_with(
            'http://192.168.23.2:5000/api/v1.0/configurations')
