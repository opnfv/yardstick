#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.dispatcher.influxdb

from __future__ import absolute_import
import unittest


try:
    from unittest import mock
except ImportError:
    import mock

from yardstick import _init_logging
_init_logging()

from yardstick.dispatcher.influxdb import InfluxdbDispatcher


class InfluxdbDispatcherTestCase(unittest.TestCase):

    def setUp(self):
        self.data1 = {
            "runner_id": 8921,
            "context_cfg": {
                "host": {
                    "ip": "10.229.43.154",
                    "key_filename":
                        "/root/yardstick/yardstick/resources/files"
                        "/yardstick_key",
                    "name": "kvm.LF",
                    "user": "root"
                },
                "target": {
                    "ipaddr": "10.229.44.134"
                }
            },
            "scenario_cfg": {
                "runner": {
                    "interval": 1,
                    "object": "yardstick.benchmark.scenarios.networking.ping"
                              ".Ping",
                    "output_filename": "/tmp/yardstick.out",
                    "runner_id": 8921,
                    "duration": 10,
                    "type": "Duration"
                },
                "host": "kvm.LF",
                "type": "Ping",
                "target": "10.229.44.134",
                "sla": {
                    "action": "monitor",
                    "max_rtt": 10
                },
                "tc": "ping",
                "task_id": "ea958583-c91e-461a-af14-2a7f9d7f79e7"
            }
        }
        self.data2 = {
            "benchmark": {
                "timestamp": "1451478117.883505",
                "errors": "",
                "data": {
                    "rtt": 0.613
                },
                "sequence": 1
            },
            "runner_id": 8921
        }

        self.yardstick_conf = {'dispatcher_influxdb': {}}

    @mock.patch('yardstick.dispatcher.influxdb.requests')
    def test_record_result_data(self, mock_requests):
        type(mock_requests.post.return_value).status_code = 204
        influxdb = InfluxdbDispatcher(self.yardstick_conf)
        data = {
            'status': 1,
            'result': {
                'criteria': 'PASS',
                'info': {
                },
                'task_id': 'b9e2bbc2-dfd8-410d-8c24-07771e9f7979',
                'testcases': {
                }
            }
        }
        self.assertEqual(influxdb.flush_result_data(data), 0)

    def test__get_nano_timestamp(self):
        influxdb = InfluxdbDispatcher(self.yardstick_conf)
        results = {'timestamp': '1451461248.925574'}
        self.assertEqual(influxdb._get_nano_timestamp(results),
                         '1451461248925574144')

    @mock.patch('yardstick.dispatcher.influxdb.time')
    def test__get_nano_timestamp_except(self, mock_time):
        results = {}
        influxdb = InfluxdbDispatcher(self.yardstick_conf)
        mock_time.time.return_value = 1451461248.925574
        self.assertEqual(influxdb._get_nano_timestamp(results),
                         '1451461248925574144')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
