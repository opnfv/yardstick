##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.dispatcher.influxdb

import mock
import unittest

from yardstick.dispatcher.influxdb import InfluxdbDispatcher
from yardstick import _init_logging


_init_logging()


class InfluxdbDispatcherTestCase(unittest.TestCase):

    def setUp(self):
        self.yardstick_conf = {'dispatcher_influxdb': {}}

    @mock.patch('yardstick.dispatcher.influxdb.requests')
    def test_flush_result_data(self, mock_requests):
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

    def test__get_extended_tags(self):
        influxdb = InfluxdbDispatcher(self.yardstick_conf)
        criteria = 'PASS'
        tags = {
            'task_id': None,
            'criteria': 'PASS'
        }
        self.assertEqual(influxdb._get_extended_tags(criteria), tags)
