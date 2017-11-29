#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for
# yardstick.benchmark.scenarios.availability.monitor.monitor_process

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.monitor import monitor_process


@mock.patch(
    'yardstick.benchmark.scenarios.availability.monitor.monitor_process.ssh')
class MonitorProcessTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.monitor_cfg = {
            'monitor_type': 'process',
            'process_name': 'nova-api',
            'host': "node1",
            'monitor_time': 1,
            'sla': {'max_recover_time': 5}
        }

    def test__monitor_process_all_successful(self, mock_ssh):

        ins = monitor_process.MonitorProcess(self.monitor_cfg, self.context, {"nova-api": 10})

        mock_ssh.SSH.from_node().execute.return_value = (0, "1", '')
        ins.setup()
        ins.monitor_func()
        ins._result = {"outage_time": 0}
        ins.verify_SLA()

    def test__monitor_process_down_failuer(self, mock_ssh):

        ins = monitor_process.MonitorProcess(self.monitor_cfg, self.context, {"nova-api": 10})

        mock_ssh.SSH.from_node().execute.return_value = (0, "0", '')
        ins.setup()
        ins.monitor_func()
        ins._result = {"outage_time": 10}
        ins.verify_SLA()
