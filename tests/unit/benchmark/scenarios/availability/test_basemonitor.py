#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.monitor

import mock
import unittest

from yardstick.benchmark.scenarios.availability.monitor import basemonitor

class MonitorMgrTestCase(unittest.TestCase):

    def setUp(self):
        config = {
            'monitor_api': 'nova image-list',
            'monitor_type': 'openstack-api',
            'instance_count': 5
        }

        self.monitor_configs = []
        self.monitor_configs.append(config)

    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.MonitorGroup')
    def test__MonitorMgr_setup_successful(self, mock_monitor_group):
        monitor_instance = basemonitor.MonitorMgr()
        monitor_instance.setup(self.monitor_configs)

        monitor_count = len(monitor_instance._monitor_list)

        self.assertEqual(monitor_count, 1)

    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.MonitorGroup')
    def test__MonitorMgr_getresult_successful(self, mock_monitor_group):
        print "test_MonitorMgr"
        monitor_instance = basemonitor.MonitorMgr()
        monitor_instance.setup(self.monitor_configs)

        monitor_instance.do_monitor()
        monitor_instance.stop_monitor()

        result = {
            "total_time": 2,
            "outage_time": 0,
            "total_count": 2,
            "outage_count": 0
        }
        mock_monitor_group().get_result.return_value = result

        ret = monitor_instance.get_result()
        self.assertEqual(result, ret)


class MonitorGroupTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.multiprocessing')
    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.BaseMonitor')
    def test__MonitorGroup_all_successful(self, mock_base_monitor, mock_multiprocessing):
        print "mock_base_monitor", mock_base_monitor
        self.monitor_config = {
            'monitor_api': 'nova image-list',
            'monitor_type': 'openstack-api',
            'instance_count': 1
        }
        monitor_instance = basemonitor.MonitorGroup()

        mock_base_monitor.get_monitor_cls.return_value = mock_base_monitor
        monitor_instance.setup(self.monitor_config)

        monitor_count = len(monitor_instance._monitor_list)
        self.assertEqual(monitor_count, 1)


        monitor_instance.start_monitor()

        result = {
            "total_time": 2,
            "outage_time": 0,
            "total_count": 2,
            "outage_count": 0
        }

        mock_multiprocessing.Queue().get.return_value = result
        monitor_instance.stop_monitor()

        ret = monitor_instance.get_result()
        self.assertEqual(result, ret)


class BaseMonitorTestCase(unittest.TestCase):

    def test__BaseMonitor_get_monitor_cls_successful(self):

        cls = basemonitor.BaseMonitor.get_monitor_cls("openstack-api")
        self.assertIsNotNone(cls)

    def test__BaseMonitor_get_monitor_cls_failure(self):
        cls = None
        try:
            cls = basemonitor.BaseMonitor.get_monitor_cls("error-monitor-type")
        except Exception:
            pass
        self.assertIsNone(cls)


class MonitorProcessFunTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.multiprocessing')
    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.BaseMonitor')
    def test__fun_monitor_process_exit_stats_error(self, mock_base_monitor, mock_multiprocessing):
        config = {
            'wait_time': 0,
            'duration': 0,
            'max_time': 0
        }

        mock_base_monitor().one_request.return_value = "error"
        mock_multiprocessing.Event().is_set.return_value = True

        basemonitor._monitor_process(mock_base_monitor, config, mock_multiprocessing.Queue(), mock_multiprocessing.Event())

    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.multiprocessing')
    @mock.patch('yardstick.benchmark.scenarios.availability.monitor.basemonitor.BaseMonitor')
    def test__fun_monitor_process_maxtime_duration(self, mock_base_monitor, mock_multiprocessing):
        config = {
            'wait_time': 0.1,
            'duration': 0.1,
            'max_time': 0.2
        }

        mock_base_monitor().one_request.return_value = None
        mock_multiprocessing.Event().is_set.return_value = False

        basemonitor._monitor_process(mock_base_monitor, config, mock_multiprocessing.Queue(), mock_multiprocessing.Event())
