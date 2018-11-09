##############################################################################
# Copyright (c) 2017 Rajesh Kudaka.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest
import uuid

from api.utils import influx
from yardstick.benchmark.core import report
from yardstick.cmd.commands import change_osloobj_to_paras

GOOD_YAML_NAME = 'fake_name'
GOOD_TASK_ID = str(uuid.uuid4())
GOOD_DB_FIELDKEYS = [{'fieldKey': 'fake_key'}]
GOOD_DB_TASK = [{
        'fake_key': 0.000,
        'time': '0000-00-00T00:00:00.000000Z',
        }]
# TODO: Rename or remove
FAKE_TIMESTAMP = ['fake_time']
BAD_TASK_ID = 'aaaaaa-aaaaaaaa-aaaaaaaaaa-aaaaaa'


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

        self.assertEqual(self.jstree.created_nodes, ['tg__0', 'tg__0.DropPackets'])
        self.assertEqual(self.jstree.jstree_data, expected_data)

    def test_format_for_jstree(self):
        data = [
            {'data': [0, ], 'name': 'tg__0.DropPackets'},
            {'data': [548, ], 'name': 'tg__0.LatencyAvg.5'},
            {'data': [1172, ], 'name': 'tg__0.LatencyAvg.6'},
            {'data': [1001, ], 'name': 'tg__0.LatencyMax.5'},
            {'data': [1468, ], 'name': 'tg__0.LatencyMax.6'},
            {'data': [18.11, ], 'name': 'tg__0.RxThroughput'},
            {'data': [18.11, ], 'name': 'tg__0.TxThroughput'},
            {'data': [0, ], 'name': 'tg__1.DropPackets'},
            {'data': [548, ], 'name': 'tg__1.LatencyAvg.5'},
            {'data': [1172, ], 'name': 'tg__1.LatencyAvg.6'},
            {'data': [1001, ], 'name': 'tg__1.LatencyMax.5'},
            {'data': [1468, ], 'name': 'tg__1.LatencyMax.6'},
            {'data': [18.1132084505, ], 'name': 'tg__1.RxThroughput'},
            {'data': [18.1157260383, ], 'name': 'tg__1.TxThroughput'},
            {'data': [9057888, ], 'name': 'vnf__0.curr_packets_in'},
            {'data': [0, ], 'name': 'vnf__0.packets_dropped'},
            {'data': [617825443, ], 'name': 'vnf__0.packets_fwd'},
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
        with self.assertRaisesRegexp(ValueError, "yaml*"):
            self.rep._validate('F@KE_NAME', GOOD_TASK_ID)

    def test__validate_invalid_task_id(self):
        with self.assertRaisesRegexp(ValueError, "task*"):
            self.rep._validate(GOOD_YAML_NAME, BAD_TASK_ID)

    @mock.patch.object(influx, 'query')
    def test__get_field_keys(self, mock_query):
        mock_query.return_value = GOOD_DB_FIELDKEYS
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.assertEqual(GOOD_DB_FIELDKEYS, self.rep._get_fieldkeys())

    @mock.patch.object(influx, 'query')
    def test__get_fieldkeys_nodbclient(self, mock_query):
        mock_query.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.rep._get_fieldkeys)

    @mock.patch.object(influx, 'query')
    def test__get_fieldkeys_task_not_found(self, mock_query):
        mock_query.return_value = []
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.assertRaisesRegexp(KeyError, "Task ID", self.rep._get_fieldkeys)

    @mock.patch.object(influx, 'query')
    def test__get_tasks(self, mock_query):
        mock_query.return_value = GOOD_DB_TASK
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.assertEqual(GOOD_DB_TASK, self.rep._get_tasks())

    @mock.patch.object(influx, 'query')
    def test__get_tasks_task_not_found(self, mock_query):
        mock_query.return_value = []
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.assertRaisesRegexp(KeyError, "Task ID", self.rep._get_tasks)

    @mock.patch.object(report.Report, '_get_tasks')
    @mock.patch.object(report.Report, '_get_fieldkeys')
    @mock.patch.object(report.Report, '_validate')
    def test_generate(self, mock_valid, mock_keys, mock_tasks):
        mock_tasks.return_value = GOOD_DB_TASK
        mock_keys.return_value = GOOD_DB_FIELDKEYS
        self.rep.generate(self.param)
        mock_valid.assert_called_once_with(GOOD_YAML_NAME, GOOD_TASK_ID)
        mock_tasks.assert_called_once_with()
        mock_keys.assert_called_once_with()
