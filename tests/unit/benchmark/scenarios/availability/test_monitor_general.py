#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.monitor
# .monitor_general

from __future__ import absolute_import
import mock
import unittest
from yardstick.benchmark.scenarios.availability.monitor import monitor_general


@mock.patch('yardstick.benchmark.scenarios.availability.monitor.'
            'monitor_general.ssh')
@mock.patch('yardstick.benchmark.scenarios.availability.monitor.'
            'monitor_general.open')
class GeneralMonitorServiceTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.monitor_cfg = {
            'monitor_type': 'general-monitor',
            'key': 'service-status',
            'monitor_key': 'service-status',
            'host': 'node1',
            'monitor_time': 3,
            'parameter': {'serviceName': 'haproxy'},
            'sla': {'max_outage_time': 1}
        }
        self.monitor_cfg_noparam = {
            'monitor_type': 'general-monitor',
            'key': 'service-status',
            'monitor_key': 'service-status',
            'host': 'node1',
            'monitor_time': 3,
            'sla': {'max_outage_time': 1}
        }

    def test__monitor_general_all_successful(self, mock_open, mock_ssh):
        ins = monitor_general.GeneralMonitor(self.monitor_cfg, self.context, {"nova-api": 10})

        ins.setup()
        mock_ssh.SSH.from_node().execute.return_value = (0, "running", '')
        ins.monitor_func()
        ins._result = {'outage_time': 0}
        ins.verify_SLA()

    def test__monitor_general_all_successful_noparam(self, mock_open,
                                                     mock_ssh):
        ins = monitor_general.GeneralMonitor(
            self.monitor_cfg_noparam, self.context, {"nova-api": 10})

        ins.setup()
        mock_ssh.SSH.from_node().execute.return_value = (0, "running", '')
        ins.monitor_func()
        ins._result = {'outage_time': 0}
        ins.verify_SLA()

    def test__monitor_general_failure(self, mock_open, mock_ssh):
        ins = monitor_general.GeneralMonitor(
            self.monitor_cfg_noparam, self.context, {"nova-api": 10})

        ins.setup()
        mock_ssh.SSH.from_node().execute.return_value = (1, "error", 'error')
        ins.monitor_func()
        ins._result = {'outage_time': 2}
        ins.verify_SLA()
