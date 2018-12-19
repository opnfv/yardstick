##############################################################################
# Copyright (c) 2017 Rajesh Kudaka.
# Copyright (c) 2018 Intel Corporation.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import six
import unittest
import uuid

from api.utils import influx
from yardstick.benchmark.core import report
from yardstick.cmd.commands import change_osloobj_to_paras

GOOD_YAML_NAME = 'fake_name'
GOOD_TASK_ID = str(uuid.uuid4())
GOOD_DB_FIELDKEYS = [{'fieldKey': 'fake_key'}]
GOOD_DB_METRICS = [{
        'fake_key': 1.234,
        'time': '0000-00-00T12:34:56.789012Z',
        }]
GOOD_TIMESTAMP = ['12:34:56.789012']
BAD_YAML_NAME = 'F@KE_NAME'
BAD_TASK_ID = 'aaaaaa-aaaaaaaa-aaaaaaaaaa-aaaaaa'
MORE_DB_FIELDKEYS = [
        {'fieldKey': 'fake_key'},
        {'fieldKey': 'str_str'},
        {'fieldKey': u'str_unicode'},
        {u'fieldKey': 'unicode_str'},
        {u'fieldKey': u'unicode_unicode'},
        ]
MORE_DB_METRICS = [{
        'fake_key': None,
        'time': '0000-00-00T00:00:00.000000Z',
        }, {
        'fake_key': 123,
        'time': '0000-00-00T00:00:01.000000Z',
        }, {
        'fake_key': 4.56,
        'time': '0000-00-00T00:00:02.000000Z',
        }, {
        'fake_key': 9876543210987654321,
        'time': '0000-00-00T00:00:03.000000Z',
        }, {
        'fake_key': 'str_str value',
        'time': '0000-00-00T00:00:04.000000Z',
        }, {
        'fake_key': u'str_unicode value',
        'time': '0000-00-00T00:00:05.000000Z',
        }, {
        u'fake_key': 'unicode_str value',
        'time': '0000-00-00T00:00:06.000000Z',
        }, {
        u'fake_key': u'unicode_unicode value',
        'time': '0000-00-00T00:00:07.000000Z',
        }, {
        'fake_key': '7.89',
        'time': '0000-00-00T00:00:08.000000Z',
        }, {
        'fake_key': '1011',
        'time': '0000-00-00T00:00:09.000000Z',
        }, {
        'fake_key': '9876543210123456789',
        'time': '0000-00-00T00:00:10.000000Z',
        }]
MORE_TIMESTAMP = ['00:00:%02d.000000' % n for n in range(len(MORE_DB_METRICS))]
MORE_EMPTY_DATA = [None] * len(MORE_DB_METRICS)
MORE_EXPECTED_TABLE_VALS = {
        'Timestamp': MORE_TIMESTAMP,
        'fake_key': [
            None,
            123,
            4.56,
            9876543210987654321 if six.PY3 else 9.876543210987655e+18,
            'str_str value',
            'str_unicode value',
            'unicode_str value',
            'unicode_unicode value',
            7.89,
            1011,
            9876543210123456789 if six.PY3 else 9.876543210123457e+18,
            ],
        'str_str': MORE_EMPTY_DATA,
        'str_unicode': MORE_EMPTY_DATA,
        'unicode_str': MORE_EMPTY_DATA,
        'unicode_unicode': MORE_EMPTY_DATA,
        }
MORE_EXPECTED_DATASETS = [{
        'label': key,
        'data': MORE_EXPECTED_TABLE_VALS[key],
        }
        for key in map(str, [field['fieldKey'] for field in MORE_DB_FIELDKEYS])
        ]


class JSTreeTestCase(unittest.TestCase):

    def setUp(self):
        self.jstree = report.JSTree()

    def test__create_node(self):
        _id = "tg__0.DropPackets"

        expected_data = [
            {"id": "tg__0", "text": "tg__0", "parent": "#"},
            {"id": "tg__0.DropPackets", "text": "DropPackets", "parent": "tg__0"}
        ]
        self.jstree._create_node(_id)

        self.assertEqual(self.jstree._created_nodes, ['#', 'tg__0', 'tg__0.DropPackets'])
        self.assertEqual(self.jstree.jstree_data, expected_data)

    def test_format_for_jstree(self):
        data = [
            'tg__0.DropPackets',
            'tg__0.LatencyAvg.5', 'tg__0.LatencyAvg.6',
            'tg__0.LatencyMax.5', 'tg__0.LatencyMax.6',
            'tg__0.RxThroughput', 'tg__0.TxThroughput',
            'tg__1.DropPackets',
            'tg__1.LatencyAvg.5', 'tg__1.LatencyAvg.6',
            'tg__1.LatencyMax.5', 'tg__1.LatencyMax.6',
            'tg__1.RxThroughput', 'tg__1.TxThroughput',
            'vnf__0.curr_packets_in', 'vnf__0.packets_dropped', 'vnf__0.packets_fwd',
        ]

        expected_output = [
            {"id": "tg__0", "text": "tg__0", "parent": "#"},
                {"id": "tg__0.DropPackets", "text": "DropPackets", "parent": "tg__0"},
                {"id": "tg__0.LatencyAvg", "text": "LatencyAvg", "parent": "tg__0"},
                    {"id": "tg__0.LatencyAvg.5", "text": "5", "parent": "tg__0.LatencyAvg"},
                    {"id": "tg__0.LatencyAvg.6", "text": "6", "parent": "tg__0.LatencyAvg"},
                {"id": "tg__0.LatencyMax", "text": "LatencyMax", "parent": "tg__0"},
                    {"id": "tg__0.LatencyMax.5", "text": "5", "parent": "tg__0.LatencyMax"},
                    {"id": "tg__0.LatencyMax.6", "text": "6", "parent": "tg__0.LatencyMax"},
                {"id": "tg__0.RxThroughput", "text": "RxThroughput", "parent": "tg__0"},
                {"id": "tg__0.TxThroughput", "text": "TxThroughput", "parent": "tg__0"},
            {"id": "tg__1", "text": "tg__1", "parent": "#"},
                {"id": "tg__1.DropPackets", "text": "DropPackets", "parent": "tg__1"},
                {"id": "tg__1.LatencyAvg", "text": "LatencyAvg", "parent": "tg__1"},
                    {"id": "tg__1.LatencyAvg.5", "text": "5", "parent": "tg__1.LatencyAvg"},
                    {"id": "tg__1.LatencyAvg.6", "text": "6", "parent": "tg__1.LatencyAvg"},
                {"id": "tg__1.LatencyMax", "text": "LatencyMax", "parent": "tg__1"},
                    {"id": "tg__1.LatencyMax.5", "text": "5", "parent": "tg__1.LatencyMax"},
                    {"id": "tg__1.LatencyMax.6", "text": "6", "parent": "tg__1.LatencyMax"},
                {"id": "tg__1.RxThroughput", "text": "RxThroughput", "parent": "tg__1"},
                {"id": "tg__1.TxThroughput", "text": "TxThroughput", "parent": "tg__1"},
            {"id": "vnf__0", "text": "vnf__0", "parent": "#"},
                {"id": "vnf__0.curr_packets_in", "text": "curr_packets_in", "parent": "vnf__0"},
                {"id": "vnf__0.packets_dropped", "text": "packets_dropped", "parent": "vnf__0"},
                {"id": "vnf__0.packets_fwd", "text": "packets_fwd", "parent": "vnf__0"},
        ]

        result = self.jstree.format_for_jstree(data)
        self.assertEqual(expected_output, result)


class ReportTestCase(unittest.TestCase):

    def setUp(self):
        super(ReportTestCase, self).setUp()
        self.param = change_osloobj_to_paras({})
        self.param.yaml_name = [GOOD_YAML_NAME]
        self.param.task_id = [GOOD_TASK_ID]
        self.rep = report.Report()

    def test___init__(self):
        self.assertEqual([], self.rep.Timestamp)
        self.assertEqual("", self.rep.yaml_name)
        self.assertEqual("", self.rep.task_id)

    def test__validate(self):
        self.rep._validate(GOOD_YAML_NAME, GOOD_TASK_ID)
        self.assertEqual(GOOD_YAML_NAME, self.rep.yaml_name)
        self.assertEqual(GOOD_TASK_ID, str(self.rep.task_id))

    def test__validate_invalid_yaml_name(self):
        with six.assertRaisesRegex(self, ValueError, "yaml*"):
            self.rep._validate(BAD_YAML_NAME, GOOD_TASK_ID)

    def test__validate_invalid_task_id(self):
        with six.assertRaisesRegex(self, ValueError, "task*"):
            self.rep._validate(GOOD_YAML_NAME, BAD_TASK_ID)

    @mock.patch.object(influx, 'query')
    def test__get_fieldkeys(self, mock_query):
        mock_query.return_value = GOOD_DB_FIELDKEYS
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.assertEqual(GOOD_DB_FIELDKEYS, self.rep._get_fieldkeys())

    @mock.patch.object(influx, 'query')
    def test__get_fieldkeys_nodbclient(self, mock_query):
        mock_query.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.rep._get_fieldkeys)

    @mock.patch.object(influx, 'query')
    def test__get_fieldkeys_testcase_not_found(self, mock_query):
        mock_query.return_value = []
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        six.assertRaisesRegex(self, KeyError, "Test case", self.rep._get_fieldkeys)

    @mock.patch.object(influx, 'query')
    def test__get_metrics(self, mock_query):
        mock_query.return_value = GOOD_DB_METRICS
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.assertEqual(GOOD_DB_METRICS, self.rep._get_metrics())

    @mock.patch.object(influx, 'query')
    def test__get_metrics_task_not_found(self, mock_query):
        mock_query.return_value = []
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        six.assertRaisesRegex(self, KeyError, "Task ID", self.rep._get_metrics)

    @mock.patch.object(report.Report, '_get_metrics')
    @mock.patch.object(report.Report, '_get_fieldkeys')
    def test__generate_common(self, mock_keys, mock_metrics):
        mock_metrics.return_value = MORE_DB_METRICS
        mock_keys.return_value = MORE_DB_FIELDKEYS
        datasets, table_vals = self.rep._generate_common(self.param)
        self.assertEqual(MORE_EXPECTED_DATASETS, datasets)
        self.assertEqual(MORE_EXPECTED_TABLE_VALS, table_vals)

    @mock.patch.object(report.Report, '_get_metrics')
    @mock.patch.object(report.Report, '_get_fieldkeys')
    @mock.patch.object(report.Report, '_validate')
    def test_generate(self, mock_valid, mock_keys, mock_metrics):
        mock_metrics.return_value = GOOD_DB_METRICS
        mock_keys.return_value = GOOD_DB_FIELDKEYS
        self.rep.generate(self.param)
        mock_valid.assert_called_once_with(GOOD_YAML_NAME, GOOD_TASK_ID)
        mock_metrics.assert_called_once_with()
        mock_keys.assert_called_once_with()
        self.assertEqual(GOOD_TIMESTAMP, self.rep.Timestamp)

    @mock.patch.object(report.Report, '_get_metrics')
    @mock.patch.object(report.Report, '_get_fieldkeys')
    @mock.patch.object(report.Report, '_validate')
    def test_generate_nsb(self, mock_valid, mock_keys, mock_metrics):
        mock_metrics.return_value = GOOD_DB_METRICS
        mock_keys.return_value = GOOD_DB_FIELDKEYS
        self.rep.generate_nsb(self.param)
        mock_valid.assert_called_once_with(GOOD_YAML_NAME, GOOD_TASK_ID)
        mock_metrics.assert_called_once_with()
        mock_keys.assert_called_once_with()
        self.assertEqual(GOOD_TIMESTAMP, self.rep.Timestamp)
