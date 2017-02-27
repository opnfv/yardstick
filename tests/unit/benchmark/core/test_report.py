#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Rajesh Kudaka.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.core.report

from __future__ import print_function

from __future__ import absolute_import

import unittest
import uuid

try:
    from unittest import mock
except ImportError:
    import mock

from yardstick.benchmark.core import report
from yardstick.cmd.commands import change_osloobj_to_paras

FAKE_YAML_NAME = 'fake_name'
FAKE_TASK_ID = str(uuid.uuid4())
FAKE_DB_FIELDKEYS = [{'fieldKey': 'fake_key'}]
FAKE_TIME = '0000-00-00T00:00:00.000000Z'
FAKE_DB_TASK = [{'fake_key': 0.000, 'time': FAKE_TIME}]
FAKE_TIMESTAMP = ['fake_time']
DUMMY_TASK_ID = 'aaaaaa-aaaaaaaa-aaaaaaaaaa-aaaaaa'


class ReportTestCase(unittest.TestCase):

    def setUp(self):
        super(ReportTestCase, self).setUp()
        self.param = change_osloobj_to_paras({})
        self.param.yaml_name = [FAKE_YAML_NAME]
        self.param.task_id = [FAKE_TASK_ID]
        self.rep = report.Report()

    @mock.patch('yardstick.benchmark.core.report.Report._get_tasks')
    @mock.patch('yardstick.benchmark.core.report.Report._get_fieldkeys')
    @mock.patch('yardstick.benchmark.core.report.Report._validate')
    def test_generate_success(self, mock_valid, mock_keys, mock_tasks):
        mock_tasks.return_value = FAKE_DB_TASK
        mock_keys.return_value = FAKE_DB_FIELDKEYS
        self.rep.generate(self.param)
        mock_valid.assert_called_once_with(FAKE_YAML_NAME, FAKE_TASK_ID)
        self.assertEqual(1, mock_tasks.call_count)
        self.assertEqual(1, mock_keys.call_count)

    def test_invalid_yaml_name(self):
        self.assertRaisesRegexp(ValueError, "yaml*", self.rep._validate,
                                'F@KE_NAME', FAKE_TASK_ID)

    def test_invalid_task_id(self):
        self.assertRaisesRegexp(ValueError, "task*", self.rep._validate,
                                FAKE_YAML_NAME, DUMMY_TASK_ID)

    @mock.patch('api.utils.influx.query')
    def test_task_not_found(self, mock_query):
        mock_query.return_value = []
        self.rep.yaml_name = FAKE_YAML_NAME
        self.rep.task_id = FAKE_TASK_ID
        self.assertRaisesRegexp(KeyError, "Task ID", self.rep._get_fieldkeys)
        self.assertRaisesRegexp(KeyError, "Task ID", self.rep._get_tasks)
