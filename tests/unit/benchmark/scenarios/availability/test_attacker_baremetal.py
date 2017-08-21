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
# yardstick.benchmark.scenarios.availability.attacker.attacker_baremetal

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.attacker import \
    attacker_baremetal


@mock.patch('yardstick.benchmark.scenarios.availability.attacker.attacker_baremetal.subprocess')
class ExecuteShellTestCase(unittest.TestCase):

    def test__fun_execute_shell_command_successful(self, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.return_value = (0, 'unittest')
        exitcode, output = attacker_baremetal._execute_shell_command(cmd)
        self.assertEqual(exitcode, 0)

    @mock.patch('yardstick.benchmark.scenarios.availability.attacker.attacker_baremetal.LOG')
    def test__fun_execute_shell_command_fail_cmd_exception(self, mock_log, mock_subprocess):
        cmd = "env"
        mock_subprocess.check_output.side_effect = RuntimeError
        exitcode, output = attacker_baremetal._execute_shell_command(cmd)
        self.assertEqual(exitcode, -1)
        mock_log.error.assert_called_once()


@mock.patch('yardstick.benchmark.scenarios.availability.attacker.attacker_baremetal.subprocess')
@mock.patch('yardstick.benchmark.scenarios.availability.attacker.attacker_baremetal.ssh')
class AttackerBaremetalTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ipmi_ip": "10.20.0.5",
            "ipmi_user": "root",
            "ipmi_pwd": "123456",
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.attacker_cfg = {
            'fault_type': 'bear-metal-down',
            'host': 'node1',
        }

    def test__attacker_baremetal_all_successful(self, mock_ssh, mock_subprocess):
        mock_ssh.SSH.from_node().execute.return_value = (0, "running", '')
        ins = attacker_baremetal.BaremetalAttacker(self.attacker_cfg,
                                                   self.context)

        ins.setup()
        ins.inject_fault()
        ins.recover()

    def test__attacker_baremetal_check_failuer(self, mock_ssh, mock_subprocess):
        mock_ssh.SSH.from_node().execute.return_value = (0, "error check", '')
        ins = attacker_baremetal.BaremetalAttacker(self.attacker_cfg,
                                                   self.context)
        ins.setup()

    def test__attacker_baremetal_recover_successful(self, mock_ssh, mock_subprocess):

        self.attacker_cfg["jump_host"] = 'node1'
        self.context["node1"]["pwd"] = "123456"
        mock_ssh.SSH.from_node().execute.return_value = (0, "running", '')
        ins = attacker_baremetal.BaremetalAttacker(self.attacker_cfg,
                                                   self.context)

        ins.setup()
        ins.recover()
