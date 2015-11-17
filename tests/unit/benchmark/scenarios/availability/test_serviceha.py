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

@mock.patch('yardstick.benchmark.scenarios.availability.serviceha.ssh')
class ServicehaTestCase(unittest.TestCase):

    def setUp(self):
        self.args = {
            'options':{
                'component':'nova-api',
                'fault_type':'stop-service',
                'fault_time':0
            },
            'sla':{
                'outage_time':'2'
            }
        }
        self.ctx = {
            'host': {
                'ip': '10.20.0.3',
                'user': 'cirros',
                'key_filename': 'mykey.key'
            }
        }

    def test__serviceha_setup_successful(self, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()

        self.assertEqual(p.setup_done, True)

    def test__serviceha_setup_fail_service(self, mock_ssh):

        self.args['options']['component'] = 'error'
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()

        self.assertEqual(p.setup_done, False)

    def test__serviceha_setup_fail_fault_type(self, mock_ssh):

        self.args['options']['fault_type'] = 'error'
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()

        self.assertEqual(p.setup_done, False)

    def test__serviceha_setup_fail_check(self, mock_ssh):

        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'error', '')
        p.setup()

        self.assertEqual(p.setup_done, False)

    def test__serviceha_setup_fail_script(self, mock_ssh):

        p = serviceha.ServiceHA(self.args, self.ctx)

        mock_ssh.SSH().execute.return_value = (-1, 'false', '')

        self.assertRaises(RuntimeError, p.setup)
        self.assertEqual(p.setup_done, False)

    @mock.patch('yardstick.benchmark.scenarios.availability.serviceha.monitor')
    def test__serviceha_run_successful(self, mock_monitor, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()

        monitor_result = {'total_time': 5, 'outage_time': 0, 'total_count': 16, 'outage_count': 0}
        mock_monitor.Monitor().get_result.return_value = monitor_result

        p.connection = mock_ssh.SSH()
        mock_ssh.SSH().execute.return_value = (0, 'success', '')

        result = {}
        p.run(result)
        self.assertEqual(result,{ 'outage_time': 0})

    def test__serviceha_run_fail_nosetup(self, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        p.run(None)

    @mock.patch('yardstick.benchmark.scenarios.availability.serviceha.monitor')
    def test__serviceha_run_fail_script(self, mock_monitor, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()

        monitor_result = {'total_time': 5, 'outage_time': 0, 'total_count': 16, 'outage_count': 0}
        mock_monitor.Monitor().get_result.return_value = monitor_result

        p.connection = mock_ssh.SSH()
        mock_ssh.SSH().execute.return_value = (-1, 'error', '')

        result = {}
        self.assertRaises(RuntimeError, p.run, result)

    @mock.patch('yardstick.benchmark.scenarios.availability.serviceha.monitor')
    def test__serviceha_run_fail_sla(self, mock_monitor, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()

        monitor_result = {'total_time': 10, 'outage_time': 5, 'total_count': 16, 'outage_count': 0}
        mock_monitor.Monitor().get_result.return_value = monitor_result

        p.connection = mock_ssh.SSH()
        mock_ssh.SSH().execute.return_value = (0, 'success', '')

        result = {}
        self.assertRaises(AssertionError, p.run, result)

    def test__serviceha_teardown_successful(self, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()
        p.need_teardown = True

        mock_ssh.SSH().execute.return_value = (0, 'success', '')
        p.teardown()

        self.assertEqual(p.need_teardown, False)

    def test__serviceha_teardown_fail_script(self, mock_ssh):
        p = serviceha.ServiceHA(self.args, self.ctx)
        mock_ssh.SSH().execute.return_value = (0, 'running', '')
        p.setup()
        p.need_teardown = True

        mock_ssh.SSH().execute.return_value = (-1, 'false', '')

        self.assertRaises(RuntimeError, p.teardown)

