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

import mock
import unittest
import requests
import json

from yardstick.benchmark.scenarios.storage import storperf


def mocked_requests_post(*args, **kwargs):
    class MockResponsePost:
        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

        def json(self):
            return self.content

    if args[0] == "http://StorPerf:5000/api/v1.0/configurations":
        return MockResponsePost({}, 200)
    elif args[0] == "http://StorPerf:5000/api/v1.0/jobs" and args[1] == {
                    "agent_count": "8",
                    "agent_network": "StorPerf_Agent_Network",
                    "volume_size": "10"}:
        return MockResponsePost({"job_id": "100"}, 200)
    elif args[0] == "http://StorPerf:5000/api/v1.0/jobs" and args[1] == "id=100":
        return MockResponsePost({
            "version": 1.0,
            "status": "completed",
            "start": 1448905682,
            "end": 1448905914,
            "workload": [{
                "name": "rw",
                "stats": {
                    "queue-depth": {
                        "1": {
                            "block-size": {
                                "4096": {
                                    "read": {
                                        "iops": 12191,
                                        "latency": {
                                            "min": 23,
                                            "mean": 413.87,
                                            "max": 1638
                                        }
                                    },
                                    "write": {
                                        "iops": 5234,
                                        "latency": {
                                            "min": 51,
                                            "mean": 39.98,
                                            "max": 434
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }]
        }, 200)

    return MockResponsePost({}, 404)


def mocked_requests_post_failed(*args, **kwargs):
    class MockResponsePostFailed:
        def __init__(self, json_data, status_code):
            self.content = json_data
            self.status_code = status_code

        def json(self):
            return self.content

    if args[0] == "http://StorPerf:5000/api/v1.0/configurations":
        return MockResponsePostFailed('{"message": "Set up failed"}', 400)
    elif args[0] == "http://StorPerf:5000/api/v1.0/jobs":
        return MockResponsePostFailed('{"message": "Job start failed"}', 400)

    return MockResponsePostFailed({}, 404)


def mocked_requests_delete(*args, **kwargs):
    class MockResponseDelete:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == "http://StorPerf:5000/api/v1.0/configurations":
        return MockResponseDelete({}, 200)
    elif args[0] == "http://StorPerf:5000/api/v1.0/jobs":
        return MockResponseDelete({}, 200)

    return MockResponseDelete({}, 404)


def mocked_requests_delete_failed(*args, **kwargs):
    class MockResponseDeleteFailed:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == "http://StorPerf:5000/api/v1.0/configurations":
        return MockResponseDeleteFailed({}, 400)
    elif args[0] == "http://StorPerf:5000/api/v1.0/jobs":
        return MockResponseDeleteFailed({}, 400)

    return MockResponseDeleteFailed({}, 404)


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
                side_effect=mocked_requests_post)
    def test_successful_setup(self, mock_post):
        options = {
            "agent_count": 8,
            "agent_network": 'StorPerf_Agent_Network',
            "volume_size": 10,
            "block_size": 4096,
            "queue_depth": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 900
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)

        s.setup()

        self.assertTrue(s.setup_done)

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.post',
                side_effect=mocked_requests_post_failed)
    def test_failed_setup(self, mock_post):
        options = {
            "agent_count": 8,
            "agent_network": 'StorPerf_Agent_Network',
            "volume_size": 10,
            "block_size": 4096,
            "queue_depth": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 900
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)

        self.assertRaises(AssertionError, s.setup(), self.result)

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.post',
                side_effect=mocked_requests_post)
    def test_successful_run(self, mock_post):
        options = {
            "agent_count": 8,
            "agent_network": 'StorPerf_Agent_Network',
            "volume_size": 10,
            "block_size": 4096,
            "queue_depth": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 900
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)
        s.job_completed = True

        sample_output = {
            "version": 1.0,
            "status": "completed",
            "start": 1448905682,
            "end": 1448905914,
            "workload": [{
                "name": "rw",
                "stats": {
                    "queue-depth": {
                        "1": {
                            "block-size": {
                                "4096": {
                                    "read": {
                                        "iops": 12191,
                                        "latency": {
                                            "min": 23,
                                            "mean": 413.87,
                                            "max": 1638
                                        }
                                    },
                                    "write": {
                                        "iops": 5234,
                                        "latency": {
                                            "min": 51,
                                            "mean": 39.98,
                                            "max": 434
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }]
        }

        expected_result = sample_output

        s.run(self.result)

        self.assertEqual(self.result, expected_result)

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.post',
                side_effect=mocked_requests_post_failed)
    def test_failed_run(self, mock_post):
        options = {
            "agent_count": 8,
            "agent_network": 'StorPerf_Agent_Network',
            "volume_size": 10,
            "block_size": 4096,
            "queue_depth": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 900
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)
        s.job_completed = True

        self.assertRaises(RuntimeError, s.run(self.result), self.result)

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.delete', side_effect=mocked_requests_delete)
    def test_successful_teardown(self, mock_delete):
        options = {
            "agent_count": 8,
            "agent_network": 'StorPerf_Agent_Network',
            "volume_size": 10,
            "block_size": 4096,
            "queue_depth": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 900
        }

        args = {
            "options": options
        }

        s = storperf.StorPerf(args, self.ctx)

        s.teardown()

        self.assertFalse(s.setup_done)

    @mock.patch('yardstick.benchmark.scenarios.storage.storperf.requests.delete', side_effect=mocked_requests_delete_failed)
    def test_failed_teardown(self, mock_delete):
        options = {
            "agent_count": 8,
            "agent_network": 'StorPerf_Agent_Network',
            "volume_size": 10,
            "block_size": 4096,
            "queue_depth": 4,
            "workload": "rs",
            "StorPerf_ip": "192.168.23.2",
            "query_interval": 10,
            "timeout": 900
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

