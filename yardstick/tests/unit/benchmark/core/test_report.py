##############################################################################
# Copyright (c) 2017 Rajesh Kudaka.
# Copyright (c) 2018-2019 Intel Corporation.
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
            None,
            None,
            None,
            None,
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

    @mock.patch.object(influx, 'query')
    def test__get_task_start_time(self, mock_query):
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        mock_query.return_value = [{
            u'free.memory0.used': u'9789088',
            u'free.memory0.available': u'22192984',
            u'free.memory0.shared': u'219152',
            u'time': u'2019-01-22T16:20:14.568075776Z',
        }]
        expected = "2019-01-22T16:20:14.568075776Z"

        self.assertEqual(
            expected,
            self.rep._get_task_start_time()
        )

    def test__get_task_start_time_task_not_found(self):
        pass

    @mock.patch.object(influx, 'query')
    def test__get_task_end_time(self, mock_query):
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        # TODO(elfoley): write this test!
        mock_query.return_value = [{

        }]

    @mock.patch.object(influx, 'query')
    def test__get_baro_metrics(self, mock_query):
        self.rep.yaml_name = GOOD_YAML_NAME
        self.rep.task_id = GOOD_TASK_ID
        self.rep._get_task_start_time = mock.Mock(return_value=0)
        self.rep._get_task_end_time = mock.Mock(return_value=0)

        influx_return_values = ([{
             u'value': 324050, u'instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:25.383698038Z',
             u'type_instance': u'user', u'type': u'cpu',
             }, {
             u'value': 193798, u'instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:25.383712594Z',
             u'type_instance': u'system', u'type': u'cpu',
             }, {
             u'value': 324051, u'instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:35.383696624Z',
             u'type_instance': u'user', u'type': u'cpu',
             }, {
             u'value': 193800, u'instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:35.383713481Z',
             u'type_instance': u'system', u'type': u'cpu',
             }, {
             u'value': 324054, u'instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:45.3836966789Z',
             u'type_instance': u'user', u'type': u'cpu',
             }, {
             u'value': 193801, u'instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:45.383716296Z',
             u'type_instance': u'system', u'type': u'cpu',
             }],
             [{
             u'value': 3598453000, u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:25.383698038Z',
             u'type_instance': u'0', u'type': u'cpufreq',
             }, {
             u'value': 3530250000, u'type_instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:35.383712594Z', u'type': u'cpufreq',
             }, {
             u'value': 3600281000, u'type_instance': u'0', u'host': u'myhostname',
             u'time': u'2018-12-19T14:11:45.383696624Z', u'type': u'cpufreq',
            }],
        )

        def ret_vals(vals):
            for x in vals:
                yield x
            while True:
                yield []

        mock_query.side_effect = ret_vals(influx_return_values)

        BARO_EXPECTED_METRICS = {
            'Timestamp': [
                '14:11:25.3836', '14:11:25.3837',
                '14:11:35.3836', '14:11:35.3837',
                '14:11:45.3836', '14:11:45.3837'],
            'myhostname.cpu_value.cpu.user.0': {
                '14:11:25.3836': 324050,
                '14:11:35.3836': 324051,
                '14:11:45.3836': 324054,
            },
            'myhostname.cpu_value.cpu.system.0': {
                '14:11:25.3837': 193798,
                '14:11:35.3837': 193800,
                '14:11:45.3837': 193801,
            },
            'myhostname.cpufreq_value.cpufreq.0': {
                '14:11:25.3836': 3598453000,
                '14:11:35.3837': 3530250000,
                '14:11:45.3836': 3600281000,
            }
        }
        self.maxDiff = None
        self.assertEqual(
            BARO_EXPECTED_METRICS,
            self.rep._get_baro_metrics()
        )

    def test__get_timestamps(self):

        metrics = MORE_DB_METRICS
        self.assertEqual(
            MORE_TIMESTAMP,
            self.rep._get_timestamps(metrics)
        )

    def test__format_datasets(self):
        metric_name = "free.memory0.used"
        metrics = [{
            u'free.memory1.free': u'1958664',
            u'free.memory0.used': u'9789560',
            }, {
            u'free.memory1.free': u'1958228',
            u'free.memory0.used': u'9789790',
            }, {
            u'free.memory1.free': u'1956156',
            u'free.memory0.used': u'9791092',
            }, {
            u'free.memory1.free': u'1956280',
            u'free.memory0.used': u'9790796',
        }]
        self.assertEqual(
            [9789560, 9789790, 9791092, 9790796,],
            self.rep._format_datasets(metric_name, metrics)
        )

    def test__format_datasets_val_none(self):
         metric_name = "free.memory0.used"
         metrics = [{
            u'free.memory1.free': u'1958664',
            u'free.memory0.used': 9876543109876543210,
            }, {
            u'free.memory1.free': u'1958228',
            }, {
            u'free.memory1.free': u'1956156',
            u'free.memory0.used': u'9791092',
            }, {
            u'free.memory1.free': u'1956280',
            u'free.memory0.used': u'9790796',
         }]

         exp0 = 9876543109876543210 if six.PY3 else 9.876543109876543e+18
         self.assertEqual(
            [exp0, None, 9791092, 9790796],
            self.rep._format_datasets(metric_name, metrics)
         )

    def test__format_datasets_val_incompatible(self):
        metric_name = "free.memory0.used"
        metrics = [{
            u'free.memory0.used': "some incompatible value",
            }, {
        }]
        self.assertEqual(
            [None, None],
            self.rep._format_datasets(metric_name, metrics)
        )

    def test__combine_times(self):
        yard_times = [
            '00:00:00.000000',
            '00:00:01.000000',
            '00:00:02.000000',
            '00:00:06.000000',
            '00:00:08.000000',
            '00:00:09.000000',
        ]
        baro_times = [
            '00:00:01.000000',
            '00:00:03.000000',
            '00:00:04.000000',
            '00:00:05.000000',
            '00:00:07.000000',
            '00:00:10.000000',
        ]
        expected_combo = [
            '00:00:00.000000',
            '00:00:01.000000',
            '00:00:02.000000',
            '00:00:03.000000',
            '00:00:04.000000',
            '00:00:05.000000',
            '00:00:06.000000',
            '00:00:07.000000',
            '00:00:08.000000',
            '00:00:09.000000',
            '00:00:10.000000',
        ]

        actual_combo = self.rep._combine_times(yard_times, baro_times)
        self.assertEqual(len(expected_combo), len(actual_combo))

        self.assertEqual(
            expected_combo,
            actual_combo,
        )

    def test__combine_times_2(self):
        time1 = ['14:11:25.383698', '14:11:25.383712', '14:11:35.383696',]
        time2 = [
            '16:20:14.568075', '16:20:24.575083',
            '16:20:34.580989', '16:20:44.586801', ]
        time_exp = [
            '14:11:25.383698', '14:11:25.383712', '14:11:35.383696',
            '16:20:14.568075', '16:20:24.575083', '16:20:34.580989',
            '16:20:44.586801',
        ]
        self.assertEqual(time_exp, self.rep._combine_times(time1, time2))

    def test__combine_metrics(self):
        BARO_METRICS = {
            'myhostname.cpu_value.cpu.user.0': {
                '14:11:25.3836': 324050, '14:11:35.3836': 324051,
                '14:11:45.3836': 324054,
            },
            'myhostname.cpu_value.cpu.system.0': {
                '14:11:25.3837': 193798, '14:11:35.3837': 193800,
                '14:11:45.3837': 193801,
            }
        }
        BARO_TIMES = [
            '14:11:25.3836', '14:11:25.3837', '14:11:35.3836',
            '14:11:35.3837', '14:11:45.3836', '14:11:45.3837',
        ]
        YARD_METRICS = {
            'free.memory9.free': {
                '16:20:14.5680': 1958244, '16:20:24.5750': 1955964,
                '16:20:34.5809': 1956040, '16:20:44.5868': 1956428,
            },
            'free.memory7.used': {
                '16:20:14.5680': 9789068, '16:20:24.5750': 9791284,
                '16:20:34.5809': 9791228, '16:20:44.5868': 9790692,
            },
            'free.memory2.total':{
                '16:20:14.5680': 32671288, '16:20:24.5750': 32671288,
                '16:20:34.5809': 32671288, '16:20:44.5868': 32671288,
            },
            'free.memory7.free': {
                '16:20:14.5680': 1958368, '16:20:24.5750': 1956104,
                '16:20:34.5809': 1956040, '16:20:44.5868': 1956552,
            },
            'free.memory1.used': {
                '16:20:14.5680': 9788872, '16:20:24.5750': 9789212,
                '16:20:34.5809': 9791168, '16:20:44.5868': 9790996,
            },
        }
        YARD_TIMES = [
             '16:20:14.5680', '16:20:24.5750',
             '16:20:34.5809', '16:20:44.5868',
        ]

        expected_output = {
            'myhostname.cpu_value.cpu.user.0': [{
                'x': '14:11:25.3836', 'y': 324050, }, {
                'x': '14:11:35.3836', 'y': 324051, }, {
                'x': '14:11:45.3836', 'y': 324054, }],
            'myhostname.cpu_value.cpu.system.0' : [{
                'x': '14:11:25.3837', 'y': 193798, }, {
                'x': '14:11:35.3837', 'y': 193800, }, {
                'x': '14:11:45.3837', 'y': 193801, }],
            'free.memory9.free': [{
                'x': '16:20:14.5680', 'y': 1958244, }, {
                'x': '16:20:24.5750', 'y': 1955964, }, {
                'x': '16:20:34.5809', 'y': 1956040, }, {
                'x': '16:20:44.5868', 'y': 1956428, }],
            'free.memory7.used': [{
                'x': '16:20:14.5680', 'y': 9789068, }, {
                'x': '16:20:24.5750', 'y': 9791284, }, {
                'x': '16:20:34.5809', 'y': 9791228, }, {
                'x': '16:20:44.5868', 'y': 9790692, }],
            'free.memory2.total': [{
                'x': '16:20:14.5680', 'y': 32671288, }, {
                'x': '16:20:24.5750', 'y': 32671288, }, {
                'x': '16:20:34.5809', 'y': 32671288, }, {
                'x': '16:20:44.5868', 'y': 32671288, }],
            'free.memory7.free': [{
                'x': '16:20:14.5680', 'y': 1958368, }, {
                'x': '16:20:24.5750', 'y': 1956104, }, {
                'x': '16:20:34.5809', 'y': 1956040, }, {
                'x': '16:20:44.5868', 'y': 1956552, }],
           'free.memory1.used': [{
                'x': '16:20:14.5680', 'y': 9788872, }, {
                'x': '16:20:24.5750', 'y': 9789212, }, {
                'x': '16:20:34.5809', 'y': 9791168, }, {
                'x': '16:20:44.5868', 'y': 9790996, }],
           }

        actual_output, _, _ = self.rep._combine_metrics(
            BARO_METRICS, BARO_TIMES, YARD_METRICS, YARD_TIMES
        )
        self.assertEquals(
            sorted(expected_output.keys()),
            sorted(actual_output.keys())
        )

        self.assertEquals(
            expected_output,
            actual_output,
        )

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

    @mock.patch.object(report.Report, '_get_baro_metrics')
    @mock.patch.object(report.Report, '_get_metrics')
    @mock.patch.object(report.Report, '_get_fieldkeys')
    @mock.patch.object(report.Report, '_validate')
    def test_generate_nsb(
        self, mock_valid, mock_keys, mock_metrics, mock_baro_metrics):

        mock_metrics.return_value = GOOD_DB_METRICS
        mock_keys.return_value = GOOD_DB_FIELDKEYS
        BARO_METRICS = {
            # TODO: is timestamp needed here?
            'Timestamp': [
                '14:11:25.383698', '14:11:25.383712', '14:11:35.383696',
                '14:11:35.383713', '14:11:45.383700', '14:11:45.383716'],
            'myhostname.cpu_value.cpu.user.0': {
                '14:11:25.383698': 324050,
                '14:11:35.383696': 324051,
                '14:11:45.383700': 324054,
            },
            'myhostname.cpu_value.cpu.system.0': {
                '14:11:25.383712': 193798,
                '14:11:35.383713': 193800,
                '14:11:45.383716': 193801,
            }
        }
        mock_baro_metrics.return_value = BARO_METRICS

        self.rep.generate_nsb(self.param)
        mock_valid.assert_called_once_with(GOOD_YAML_NAME, GOOD_TASK_ID)
        mock_metrics.assert_called_once_with()
        mock_keys.assert_called_once_with()
        self.assertEqual(GOOD_TIMESTAMP, self.rep.Timestamp)
