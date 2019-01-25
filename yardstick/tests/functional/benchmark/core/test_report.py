##############################################################################
# Copyright (c) 2018-2019 Intel Corporation.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import ast
import tempfile
import unittest

import mock
from six.moves import configparser

from yardstick.benchmark import core
from yardstick.benchmark.core import report
from yardstick.cmd.commands import change_osloobj_to_paras


GOOD_YAML_NAME = 'fake_name'
GOOD_TASK_ID = "9cbe74b6-df09-4535-8bdc-dc3a43b8a4e2"
GOOD_DB_FIELDKEYS = [
    {u'fieldKey': u'metric1', u'fieldType': u'integer'},
    {u'fieldKey': u'metric4', u'fieldType': u'integer'},
    {u'fieldKey': u'metric2', u'fieldType': u'integer'},
    {u'fieldKey': u'metric3', u'fieldType': u'integer'},
]
GOOD_DB_METRICS = [
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
GOOD_DB_BARO_METRICS = [
     {u'value': 324050, u'instance': u'0', u'host': u'myhostname',
      u'time': u'2018-08-20T16:49:27.383698038Z',
      u'type_instance': u'user', u'type': u'cpu'},
     {
      u'value': 193798, u'instance': u'0', u'host': u'myhostname',
      u'time': u'2018-12-19T16:49:27.383712594Z',
      u'type_instance': u'system', u'type': u'cpu'},
     {
      u'value': 324051, u'instance': u'0', u'host': u'myhostname',
      u'time': u'2018-08-20T16:49:28.383696624Z',
      u'type_instance': u'user', u'type': u'cpu'},
     {
      u'value': 193800, u'instance': u'0', u'host': u'myhostname',
      u'time': u'2018-08-20T16:49:28.383713481Z',
      u'type_instance': u'system', u'type': u'cpu' },
     {
      u'value': 324054, u'instance': u'0', u'host': u'myhostname',
      u'time': u'2018-08-20T16:49:29.3836966789Z',
      u'type_instance': u'user', u'type': u'cpu'},
     {
      u'value': 193801, u'instance': u'0', u'host': u'myhostname',
      u'time': u'2018-08-20T16:49:29.383716296Z',
      u'type_instance': u'system', u'type': u'cpu'}
]
TIMESTAMP_START = '2018-08-20T16:49:26.372662016Z'
TIMESTAMP_END = '2018-08-20T16:49:30.379359421Z'

yardstick_config = """
[DEFAULT]
dispatcher = influxdb
"""


def my_query(query_sql, db=None):
    get_fieldkeys_cmd = 'show field keys'
    get_metrics_cmd = 'select * from'
    get_start_time_cmd = 'ORDER ASC limit 1'
    get_end_time_cmd = 'ORDER DESC limit 1'
    if db:
        if get_start_time_cmd in query_sql:
            return TIMESTAMP_START
        elif get_end_time_cmd in query_sql:
            return TIMESTAMP_END
        else:
            return GOOD_DB_BARO_METRICS
    elif get_fieldkeys_cmd in query_sql:
        return GOOD_DB_FIELDKEYS
    elif get_metrics_cmd in query_sql:
        return GOOD_DB_METRICS
    return []


class ReportTestCase(unittest.TestCase):

    @mock.patch.object(report.influx, 'query', new=my_query)
    @mock.patch.object(configparser.ConfigParser,
        'read', side_effect=mock.mock_open(read_data=yardstick_config))
    def test_report_generate_nsb_simple(self, *args):
        tmpfile = tempfile.NamedTemporaryFile(delete=True)

        args = core.Param({"task_id": [GOOD_TASK_ID], "yaml_name": [GOOD_YAML_NAME]})
        params = change_osloobj_to_paras(args)

        with mock.patch.object(report.consts, 'DEFAULT_HTML_FILE', tmpfile.name):
            report.Report().generate_nsb(params)

        data_act = None
        time_act = None
        keys_act = None
        tree_act = None
        with open(tmpfile.name) as f:
            for l in f.readlines():
                 if "var report_data = {" in l:
                     data_act = ast.literal_eval(l.strip()[18:-1])
                 elif "var report_time = [" in l:
                     time_act = ast.literal_eval(l.strip()[18:-1])
                 elif "var report_keys = [" in l:
                     keys_act = ast.literal_eval(l.strip()[18:-1])
                 elif "var report_tree = [" in l:
                     tree_act = ast.literal_eval(l.strip()[18:-1])
        data_exp = {
            'metric1': [
                {'x': '16:49:26.372662', 'y': 1},
                {'x': '16:49:27.374208', 'y': 1},
                {'x': '16:49:28.375742', 'y': 2},
                {'x': '16:49:29.377299', 'y': 3},
                {'x': '16:49:30.378252', 'y': 5},
                {'x': '16:49:30.379359', 'y': 8}],
            'metric2': [
                {'x': '16:49:26.372662', 'y': 0},
                {'x': '16:49:27.374208', 'y': 1},
                {'x': '16:49:28.375742', 'y': 2},
                {'x': '16:49:29.377299', 'y': 3},
                {'x': '16:49:30.378252', 'y': 4},
                {'x': '16:49:30.379359', 'y': 5}],
            'metric3': [
                {'x': '16:49:26.372662', 'y': 8},
                {'x': '16:49:27.374208', 'y': 5},
                {'x': '16:49:28.375742', 'y': 3},
                {'x': '16:49:29.377299', 'y': 2},
                {'x': '16:49:30.378252', 'y': 1},
                {'x': '16:49:30.379359', 'y': 1}],
            'metric4': [
                {'x': '16:49:26.372662', 'y': 5},
                {'x': '16:49:27.374208', 'y': 4},
                {'x': '16:49:28.375742', 'y': 3},
                {'x': '16:49:29.377299', 'y': 2},
                {'x': '16:49:30.378252', 'y': 1},
                {'x': '16:49:30.379359', 'y': 0}],
            'myhostname.cpu_value.cpu.system.0': [
                {'x': '16:49:27.3837', 'y': 193798},
                {'x': '16:49:28.3837', 'y': 193800},
                {'x': '16:49:29.3837', 'y': 193801}],
            'myhostname.cpu_value.cpu.user.0': [
                {'x': '16:49:27.3836', 'y': 324050},
                {'x': '16:49:28.3836', 'y': 324051},
                {'x': '16:49:29.3836', 'y': 324054}],
            'myhostname.cpufreq_value.cpu.system.0': [
                {'x': '16:49:27.3837', 'y': 193798},
                {'x': '16:49:28.3837', 'y': 193800},
                {'x': '16:49:29.3837', 'y': 193801}],
            'myhostname.cpufreq_value.cpu.user.0': [
                {'x': '16:49:27.3836', 'y': 324050},
                {'x': '16:49:28.3836', 'y': 324051},
                {'x': '16:49:29.3836', 'y': 324054}],
            'myhostname.intel_pmu_value.cpu.system.0': [
                {'x': '16:49:27.3837', 'y': 193798},
                {'x': '16:49:28.3837', 'y': 193800},
                {'x': '16:49:29.3837', 'y': 193801}],
            'myhostname.intel_pmu_value.cpu.user.0': [
                {'x': '16:49:27.3836', 'y': 324050},
                {'x': '16:49:28.3836', 'y': 324051},
                {'x': '16:49:29.3836', 'y': 324054}],
            'myhostname.virt_value.cpu.system.0': [
                {'x': '16:49:27.3837', 'y': 193798},
                {'x': '16:49:28.3837', 'y': 193800},
                {'x': '16:49:29.3837', 'y': 193801}],
            'myhostname.virt_value.cpu.user.0': [
                {'x': '16:49:27.3836', 'y': 324050},
                {'x': '16:49:28.3836', 'y': 324051},
                {'x': '16:49:29.3836', 'y': 324054}],
            'myhostname.memory_value.cpu.system.0': [
                {'x': '16:49:27.3837', 'y': 193798},
                {'x': '16:49:28.3837', 'y': 193800},
                {'x': '16:49:29.3837', 'y': 193801}],
            'myhostname.memory_value.cpu.user.0': [
                {'x': '16:49:27.3836', 'y': 324050},
                {'x': '16:49:28.3836', 'y': 324051},
                {'x': '16:49:29.3836', 'y': 324054}]
        }
        time_exp = [
            '16:49:26.372662', '16:49:27.374208', '16:49:27.3836', '16:49:27.3837', '16:49:28.375742', '16:49:28.3836', '16:49:28.3837',
            '16:49:29.377299', '16:49:29.3836', '16:49:29.3837', '16:49:30.378252', '16:49:30.379359',
        ]
        keys_exp = sorted([
            'metric1', 'metric2', 'metric3', 'metric4',
            'myhostname.cpu_value.cpu.system.0', 'myhostname.cpu_value.cpu.user.0',
            'myhostname.cpufreq_value.cpu.system.0','myhostname.cpufreq_value.cpu.user.0',
            'myhostname.intel_pmu_value.cpu.system.0','myhostname.intel_pmu_value.cpu.user.0',
            'myhostname.virt_value.cpu.system.0','myhostname.virt_value.cpu.user.0',
            'myhostname.memory_value.cpu.system.0','myhostname.memory_value.cpu.user.0',
        ])
        tree_exp = [
            {'parent': '#', 'text': 'metric1', 'id': 'metric1'},
            {'parent': '#', 'text': 'metric2', 'id': 'metric2'},
            {'parent': '#', 'text': 'metric3', 'id': 'metric3'},
            {'parent': '#', 'text': 'metric4', 'id': 'metric4'},
            {'id': 'myhostname', 'parent': '#', 'text': 'myhostname'},
            {'id': 'myhostname.cpu_value',
             'parent': 'myhostname',
             'text': 'cpu_value'},
            {'id': 'myhostname.cpu_value.cpu',
             'parent': 'myhostname.cpu_value',
             'text': 'cpu'},
            {'id': 'myhostname.cpu_value.cpu.system',
             'parent': 'myhostname.cpu_value.cpu',
             'text': 'system'},
            {'id': 'myhostname.cpu_value.cpu.system.0',
             'parent': 'myhostname.cpu_value.cpu.system',
             'text': '0'},
            {'id': 'myhostname.cpu_value.cpu.user',
             'parent': 'myhostname.cpu_value.cpu',
             'text': 'user'},
            {'id': 'myhostname.cpu_value.cpu.user.0',
             'parent': 'myhostname.cpu_value.cpu.user',
             'text': '0'},
            {'id': 'myhostname.cpufreq_value',
             'parent': 'myhostname',
             'text': 'cpufreq_value'},
            {'id': 'myhostname.cpufreq_value.cpu',
             'parent': 'myhostname.cpufreq_value',
             'text': 'cpu'},
            {'id': 'myhostname.cpufreq_value.cpu.system',
             'parent': 'myhostname.cpufreq_value.cpu',
             'text': 'system'},
            {'id': 'myhostname.cpufreq_value.cpu.system.0',
             'parent': 'myhostname.cpufreq_value.cpu.system',
             'text': '0'},
            {'id': 'myhostname.cpufreq_value.cpu.user',
             'parent': 'myhostname.cpufreq_value.cpu',
             'text': 'user'},
            {'id': 'myhostname.cpufreq_value.cpu.user.0',
             'parent': 'myhostname.cpufreq_value.cpu.user',
             'text': '0'},
            {'id': 'myhostname.intel_pmu_value',
             'parent': 'myhostname',
             'text': 'intel_pmu_value'},
            {'id': 'myhostname.intel_pmu_value.cpu',
             'parent': 'myhostname.intel_pmu_value',
             'text': 'cpu'},
            {'id': 'myhostname.intel_pmu_value.cpu.system',
             'parent': 'myhostname.intel_pmu_value.cpu',
             'text': 'system'},
            {'id': 'myhostname.intel_pmu_value.cpu.system.0',
             'parent': 'myhostname.intel_pmu_value.cpu.system',
             'text': '0'},
            {'id': 'myhostname.intel_pmu_value.cpu.user',
             'parent': 'myhostname.intel_pmu_value.cpu',
             'text': 'user'},
            {'id': 'myhostname.intel_pmu_value.cpu.user.0',
             'parent': 'myhostname.intel_pmu_value.cpu.user',
             'text': '0'},
            {'id': 'myhostname.memory_value',
             'parent': 'myhostname',
             'text': 'memory_value'},
            {'id': 'myhostname.memory_value.cpu',
             'parent': 'myhostname.memory_value',
             'text': 'cpu'},
            {'id': 'myhostname.memory_value.cpu.system',
             'parent': 'myhostname.memory_value.cpu',
             'text': 'system'},
            {'id': 'myhostname.memory_value.cpu.system.0',
             'parent': 'myhostname.memory_value.cpu.system',
             'text': '0'},
            {'id': 'myhostname.memory_value.cpu.user',
             'parent': 'myhostname.memory_value.cpu',
             'text': 'user'},
            {'id': 'myhostname.memory_value.cpu.user.0',
             'parent': 'myhostname.memory_value.cpu.user',
             'text': '0'},
            {'id': 'myhostname.virt_value', 'parent': 'myhostname',
             'text': 'virt_value'},
            {'id': 'myhostname.virt_value.cpu',
             'parent': 'myhostname.virt_value',
             'text': 'cpu'},
            {'id': 'myhostname.virt_value.cpu.system',
             'parent': 'myhostname.virt_value.cpu',
             'text': 'system'},
            {'id': 'myhostname.virt_value.cpu.system.0',
             'parent': 'myhostname.virt_value.cpu.system',
             'text': '0'},
            {'id': 'myhostname.virt_value.cpu.user',
             'parent': 'myhostname.virt_value.cpu',
             'text': 'user'},
            {'id': 'myhostname.virt_value.cpu.user.0',
             'parent': 'myhostname.virt_value.cpu.user',
             'text': '0'}
        ]

        self.assertEqual(data_exp, data_act)
        self.assertEqual(time_exp, time_act)
        self.assertEqual(keys_exp, keys_act)
        self.assertEqual(tree_exp, tree_act)
