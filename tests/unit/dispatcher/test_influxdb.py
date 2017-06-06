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
        self.data3 = {
            "benchmark": {
                "data": {
                    "mpstat": {
                        "cpu0": {
                            "%sys": "0.00",
                            "%idle": "99.00"
                        },
                        "loadavg": [
                            "1.09",
                            "0.29"
                        ]
                    },
                    "rtt": "1.03"
                }
            }
        }

        self.yardstick_conf = {'yardstick': {}}

    def test_record_result_data_no_target(self):
        influxdb = InfluxdbDispatcher(None, self.yardstick_conf)
        influxdb.target = ''
        self.assertEqual(influxdb.record_result_data(self.data1), -1)

    def test_record_result_data_no_case_name(self):
        influxdb = InfluxdbDispatcher(None, self.yardstick_conf)
        self.assertEqual(influxdb.record_result_data(self.data2), -1)

    @mock.patch('yardstick.dispatcher.influxdb.requests')
    def test_record_result_data(self, mock_requests):
        type(mock_requests.post.return_value).status_code = 204
        influxdb = InfluxdbDispatcher(None, self.yardstick_conf)
        self.assertEqual(influxdb.record_result_data(self.data1), 0)
        self.assertEqual(influxdb.record_result_data(self.data2), 0)
        self.assertEqual(influxdb.flush_result_data(), 0)

    def test__dict_key_flatten(self):
        line = 'mpstat.loadavg1=0.29,rtt=1.03,mpstat.loadavg0=1.09,' \
               'mpstat.cpu0.%idle=99.00,mpstat.cpu0.%sys=0.00'
        # need to sort for assert to work
        line = ",".join(sorted(line.split(',')))
        influxdb = InfluxdbDispatcher(None, self.yardstick_conf)
        flattened_data = influxdb._dict_key_flatten(
            self.data3['benchmark']['data'])
        result = ",".join(
            [k + "=" + v for k, v in sorted(flattened_data.items())])
        self.assertEqual(result, line)

    def test__get_nano_timestamp(self):
        influxdb = InfluxdbDispatcher(None, self.yardstick_conf)
        results = {'benchmark': {'timestamp': '1451461248.925574'}}
        self.assertEqual(influxdb._get_nano_timestamp(results),
                         '1451461248925574144')

    @mock.patch('yardstick.dispatcher.influxdb.time')
    def test__get_nano_timestamp_except(self, mock_time):
        results = {}
        influxdb = InfluxdbDispatcher(None, self.yardstick_conf)
        mock_time.time.return_value = 1451461248.925574
        self.assertEqual(influxdb._get_nano_timestamp(results),
                         '1451461248925574144')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
