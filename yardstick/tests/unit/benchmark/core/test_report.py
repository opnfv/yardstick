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
