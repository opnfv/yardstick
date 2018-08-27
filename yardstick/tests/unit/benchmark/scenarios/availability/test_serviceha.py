##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from yardstick.benchmark.scenarios.availability import serviceha
from yardstick.common import exceptions as y_exc


class ServicehaTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.ctx = {"nodes": {"node1": host}}
        attacker_cfg = {
            "fault_type": "kill-process",
            "process_name": "nova-api",
            "host": "node1"
        }
        attacker_cfgs = []
        attacker_cfgs.append(attacker_cfg)
        monitor_cfg = {
            "monitor_cmd": "nova image-list",
            "monitor_time": 0.1
        }
        monitor_cfgs = []
        monitor_cfgs.append(monitor_cfg)

        options = {
            "attackers": attacker_cfgs,
            "monitors": monitor_cfgs
        }
        sla = {"outage_time": 5}
        self.args = {"options": options, "sla": sla}
        self.test__serviceha = serviceha.ServiceHA(self.args, self.ctx)

    def test___init__(self):

        self.assertEqual(self.test__serviceha.data, {})
        self.assertFalse(self.test__serviceha.setup_done)
        self.assertFalse(self.test__serviceha.sla_pass)

    # NOTE(elfoley): This should be split into test_setup and test_run
    # NOTE(elfoley): This should explicitly test outcomes and states
    @mock.patch.object(serviceha, 'baseattacker')
    @mock.patch.object(serviceha, 'basemonitor')
    def test__serviceha_setup_run_successful(self, mock_monitor, *args):
        p = serviceha.ServiceHA(self.args, self.ctx)

        p.setup()
        self.assertTrue(p.setup_done)
        mock_monitor.MonitorMgr().verify_SLA.return_value = True
        ret = {}
        p.run(ret)
        p.teardown()

        p.setup()
        self.assertTrue(p.setup_done)

    @mock.patch.object(serviceha, 'baseattacker')
    @mock.patch.object(serviceha, 'basemonitor')
    def test__serviceha_run_sla_error(self, mock_monitor, *args):
        p = serviceha.ServiceHA(self.args, self.ctx)

        p.setup()
        self.assertEqual(p.setup_done, True)

        mock_monitor.MonitorMgr().verify_SLA.return_value = False

        ret = {}
        self.assertRaises(y_exc.SLAValidationError, p.run, ret)
        self.assertEqual(ret['sla_pass'], 0)

    @mock.patch.object(serviceha, 'baseattacker')
    @mock.patch.object(serviceha, 'basemonitor')
    def test__serviceha_run_service_not_found_sla_error(self, mock_monitor,
                                                        *args):
        p = serviceha.ServiceHA(self.args, self.ctx)

        p.setup()
        self.assertTrue(p.setup_done)
        p.data["kill-process"] = 0

        mock_monitor.MonitorMgr().verify_SLA.return_value = True

        ret = {}
        self.assertRaises(y_exc.SLAValidationError, p.run, ret)
        self.assertEqual(ret['sla_pass'], 0)

    @mock.patch.object(serviceha, 'baseattacker')
    @mock.patch.object(serviceha, 'basemonitor')
    def test__serviceha_no_teardown_when_sla_pass(self, mock_monitor,
                                                  *args):
        p = serviceha.ServiceHA(self.args, self.ctx)
        p.setup()
        self.assertTrue(p.setup_done)
        mock_monitor.MonitorMgr().verify_SLA.return_value = True
        ret = {}
        p.run(ret)
        attacker = mock.Mock()
        attacker.mandatory = False
        p.attackers = [attacker]
        p.teardown()
        attacker.recover.assert_not_called()

    @mock.patch.object(serviceha, 'baseattacker')
    @mock.patch.object(serviceha, 'basemonitor')
    def test__serviceha_teardown_when_mandatory(self, mock_monitor,
                                                *args):
        p = serviceha.ServiceHA(self.args, self.ctx)
        p.setup()
        self.assertTrue(p.setup_done)
        mock_monitor.MonitorMgr().verify_SLA.return_value = True
        ret = {}
        p.run(ret)
        attacker = mock.Mock()
        attacker.mandatory = True
        p.attackers = [attacker]
        p.teardown()
        attacker.recover.assert_called_once()
