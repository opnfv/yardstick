#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.serviceha

import mock
import unittest

from yardstick.benchmark.scenarios.availability import serviceha

@mock.patch('yardstick.benchmark.scenarios.availability.serviceha.monitor')
@mock.patch('yardstick.benchmark.scenarios.availability.serviceha.baseattacker')
class ServicehaTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.ctx = {"host": host}
        attacker_cfg = {
            "fault_type": "stop-service",
            "service_name": "nova-api",
            "fault_time": 5,
            "host": host
        }
        attacker_cfgs = []
        attacker_cfgs.append(attacker_cfg)
        monitor_cfg = {
            "monitor_type": "openstack-api",
            "monitor_api": "nova image-list"
        }
        monitor_cfgs = []
        monitor_cfgs.append(monitor_cfg)

        options = {
            "attackers": attacker_cfgs,
            "monitors": monitor_cfgs
        }
        sla = {"outage_time": 5}
        self.args = {"options": options, "sla": sla}

    def test__serviceha_setup_run_successful(self, mock_attacker, mock_monitor):
        p = serviceha.ServiceHA(self.args, self.ctx)

        p.setup()
        self.assertEqual(p.setup_done, True)

        result = {}
        result["outage_time"] = 0
        mock_monitor.Monitor().get_result.return_value = result
        ret = {}
        p.run(ret)
        self.assertEqual(ret, result)
        p.teardown()

    def test__serviceha_run_sla_error(self, mock_attacker, mock_monitor):
        p = serviceha.ServiceHA(self.args, self.ctx)

        p.setup()
        self.assertEqual(p.setup_done, True)

        result = {}
        result["outage_time"] = 10
        mock_monitor.Monitor().get_result.return_value = result

        ret = {}
        self.assertRaises(AssertionError, p.run, ret)
