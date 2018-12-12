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
import requests

from yardstick.dispatcher import influxdb
from yardstick import _init_logging


_init_logging()


class InfluxdbDispatcherTestCase(unittest.TestCase):

    def setUp(self):
        self.yardstick_conf = {'dispatcher_influxdb': {}}

    @mock.patch('yardstick.dispatcher.influxdb.requests')
    def test_flush_result_data(self, mock_requests):
        type(mock_requests.post.return_value).status_code = 204
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
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
        self.assertEqual(influx.flush_result_data(data), 0)

    @mock.patch.object(influxdb.InfluxdbDispatcher,
                       '_metadata_to_line_protocol')
    def test_upload_metadata_record_post(self, mock__metadata):
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        self.tc_name = "tc_prox"
        self.task_id = "4d978ecb-f962-47e1-9da1-2f3a35c2267e"
        self.tc_time = "2018-12-13T10:43:40.280419"
        self.mock_requests = mock.Mock()
        self.metadata = {
            'tc_time': self.tc_time,
            'tc_name': self.tc_name,
            'task_id': self.task_id,
            'table_name': "metadata_table",
        }

        mock__metadata.return_value = \
            'metadata_table,' \
            'tc_name=tc_prox,' \
            'tc_time=2018-12-13T10:43:40.280419' \
            'task_id="4d978ecb-f962-47e1-9da1-2f3a35c2267e"\n'
        self.assertIsNone(influx.upload_metadata_record(self.metadata))

    @mock.patch.object(influxdb.InfluxdbDispatcher,
                       '_metadata_to_line_protocol')
    @mock.patch.object(requests, 'post')
    @mock.patch.object(influxdb, 'LOG')
    def test_upload_metadata_record_post_exception(
            self, mock_logger, mock_requests_post, mock__metadata):
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        self.tc_name = "tc_prox"
        self.task_id = "4d978ecb-f962-47e1-9da1-2f3a35c2267e"
        self.tc_time = "2018-12-13T10:43:40.280419"
        self.metadata = {
            'tc_time': self.tc_time,
            'tc_name': self.tc_name,
            'task_id': self.task_id,
            'table_name': "metadata_table",
        }

        mock__metadata.return_value = \
            'metadata_table,' \
            'tc_name=tc_prox,' \
            'tc_time=2018-12-13T10:43:40.280419' \
            'task_id="4d978ecb-f962-47e1-9da1-2f3a35c2267e"\n'

        mock_requests_post.side_effect = (
            requests.ConnectionError('error message'))
        self.assertIsNone(influx.upload_metadata_record(self.metadata))
        mock_logger.exception.assert_called_once()

    @mock.patch.object(influxdb.InfluxdbDispatcher,
                       '_metadata_to_line_protocol')
    @mock.patch.object(requests, 'post')
    @mock.patch.object(influxdb, 'LOG')
    def test_upload_metadata_record_post_status_code(
            self, mock_logger, mock_requests_post, mock__metadata):
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        self.tc_name = "tc_prox"
        self.task_id = "4d978ecb-f962-47e1-9da1-2f3a35c2267e"
        self.tc_time = "2018-12-13T10:43:40.280419'"
        self.metadata = {
            'tc_time': self.tc_time,
            'tc_name': self.tc_name,
            'task_id': self.task_id,
            'table_name': "metadata_table",
        }

        mock__metadata.return_value = \
            'metadata_table,' \
            'tc_name=tc_prox,' \
            'tc_time=2018-12-13T10:43:40.280419' \
            'task_id="4d978ecb-f962-47e1-9da1-2f3a35c2267e"\n'

        mock_requests_post.status_code.return_value = 204
        self.assertIsNone(influx.upload_metadata_record(self.metadata))
        mock_logger.error.assert_called()

    @mock.patch.object(influxdb.InfluxdbDispatcher,
                       '_data_to_line_protocol')
    def test_upload_one_record(self, mock__data_to_line):
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        self.case = "tc_prox"
        self.tc_criteria = "pass"
        self.task_id = "4d978ecb-f962-47e1-9da1-2f3a35c2267e"
        self.data = {}
        self.mock_requests = mock.Mock()

        mock__data_to_line.return_value = \
            'tc_prox,deploy_scenario=unknown,installer=unknown,' \
            'pod_name=unknown,task_id=4d978ecb-f962-47e1-9da1-2f3a35c2267e,' \
            'version=unknown  1546530835749260544\n'

        self.assertIsNone(influx.upload_one_record(
            self.data, self.case, self.tc_criteria, self.task_id))

    def test__get_nano_timestamp(self):
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        results = {'timestamp': '1451461248.925574'}
        self.assertEqual(influx._get_nano_timestamp(results),
                         '1451461248925574144')

    @mock.patch('yardstick.dispatcher.influxdb.time')
    def test__get_nano_timestamp_except(self, mock_time):
        results = {}
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        mock_time.time.return_value = 1451461248.925574
        self.assertEqual(influx._get_nano_timestamp(results),
                         '1451461248925574144')

    def test__get_extended_tags(self):
        influx = influxdb.InfluxdbDispatcher(self.yardstick_conf)
        criteria = 'PASS'
        tags = {
            'task_id': None,
            'criteria': 'PASS'
        }
        self.assertEqual(influx._get_extended_tags(criteria), tags)
