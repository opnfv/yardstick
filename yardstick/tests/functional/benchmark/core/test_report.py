##############################################################################
# Copyright (c) 2018 Intel.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import ast
import os
import tempfile
import unittest

import mock
from six.moves import configparser

from influxdb import client as influxdb_client

from yardstick.benchmark import core
from yardstick.benchmark.core import report
from yardstick.cmd.commands import change_osloobj_to_paras


GOOD_YAML_NAME = 'fake_name'
GOOD_TASK_ID = "9cbe74b6-df09-4535-8bdc-dc3a43b8a4e2"
GOOD_DB_FIELDKEYS = [
    {u'fieldKey': u'metric1', u'fieldType': u'integer'},
    {u'fieldKey': u'metric2', u'fieldType': u'integer'},
    {u'fieldKey': u'metric3', u'fieldType': u'integer'},
    {u'fieldKey': u'metric4', u'fieldType': u'integer'},
]

GOOD_DB_TASK = [
    {u'time': u'2018-08-20T16:49:26.372662016Z',
     u'metric1': 1, u'metric2': 0, u'metric3': 8, u'metric4': 5},
    {u'time': u'2018-08-20T16:49:27.374208000Z',
     u'metric1': 1, u'metric2': 1, u'metric3': 5, u'metric4': 4},
    {u'time': u'2018-08-20T16:49:28.375742976Z',
     u'metric1': 2, u'metric2': 2, u'metric3': 3, u'metric4': 3},
    {u'time': u'2018-08-20T16:49:29.377299968Z',
     u'metric1': 3, u'metric2': 3, u'metric3': 2, u'metric4': 2},
    {u'time': u'2018-08-20T16:49:30.378252032Z',
     u'metric1': 5, u'metric2': 4, u'metric3': 1, u'metric4': 1},
    {u'time': u'2018-08-20T16:49:30.379359421Z',
     u'metric1': 8, u'metric2': 5, u'metric3': 1, u'metric4': 0},
]

yardstick_config = """
[DEFAULT]
dispatcher = influxdb
"""


def my_query(query_sql):

    get_fieldkeys_cmd = 'show field keys'
    get_tasks_cmd = 'select * from'

    if get_fieldkeys_cmd in query_sql:
        return GOOD_DB_FIELDKEYS

    elif get_tasks_cmd in query_sql:
        return GOOD_DB_TASK

    else:
        return []


class ReportTestCase(unittest.TestCase):

    @mock.patch.object(influxdb_client, 'InfluxDBClient')
    @mock.patch.object(core.report.influx, 'query', new=my_query)
    @mock.patch.object(configparser.ConfigParser,
        'read', side_effect=mock.mock_open(read_data=yardstick_config))
    def test_report_generate_nsb_simple(self, *args):
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.remove, tmpfile.name)

        args = core.Param({"task_id": [GOOD_TASK_ID], "yaml_name": [GOOD_YAML_NAME]})
        params = change_osloobj_to_paras(args)

        with mock.patch.object(report.consts, 'DEFAULT_HTML_FILE', tmpfile.name):
            report.Report().generate_nsb(params)

        #print("filename: {}".format(tmpfile.name))
        with open(tmpfile.name) as f:

            for l in f.readlines():
                 if "arr={" in l:
                     arr_act = ast.literal_eval(l.strip()[4:])
                 elif "jstree_data = [" in l:
                     jstree_data_act = ast.literal_eval(l.strip()[14:])
        print(jstree_data_act)

        arr_exp = {
            'Timestamp':
                ['16:49:26.372662', '16:49:27.374208', '16:49:28.375742',
                 '16:49:29.377299', '16:49:30.378252', '16:49:30.379359'],
            'metric4': [5, 4, 3, 2, 1, 0],
            'metric2': [0, 1, 2, 3, 4, 5],
            'metric3': [8, 5, 3, 2, 1, 1],
            'metric1': [1, 1, 2, 3, 5, 8],
        }
        jstree_data_exp = [
            {'parent': '#', 'text': 'metric1', 'id': 'metric1'},
            {'parent': '#', 'text': 'metric2', 'id': 'metric2'},
            {'parent': '#', 'text': 'metric3', 'id': 'metric3'},
            {'parent': '#', 'text': 'metric4', 'id': 'metric4'},
        ]

        self.assertEqual(arr_exp, arr_act)
        def _comp(l1, l2):
            if not len(l1) == len(l2):
                return False
            for d in l1:
                if not d in l2:
                    return False
            return True

        self.assertTrue(_comp(jstree_data_exp, jstree_data_act))
