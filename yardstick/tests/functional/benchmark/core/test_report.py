##############################################################################
# Copyright (c) 2018 Intel.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest
import uuid

from six.moves import builtins
from six.moves import configparser
import tempfile

from influxdb import client as influxdb_client

from yardstick.benchmark import core
from yardstick.benchmark.core import report
from yardstick.cmd.commands import change_osloobj_to_paras


GOOD_YAML_NAME = 'fake_name'
GOOD_TASK_ID = str(uuid.uuid4())
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
    def test_report_generate_nsb(self, mock_parser_read, mock_influxdbclient):
        args = core.Param({"task_id": [GOOD_TASK_ID], "yaml_name": [GOOD_YAML_NAME]})
        params = change_osloobj_to_paras(args)

        #with mock.patch.object(builtins, 'open', new=tempfile.NamedTemporaryFile) as mock_open:
        report.Report().generate_nsb(params)
        # replace write with write_temp??
