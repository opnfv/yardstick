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

from yardstick.benchmark.scenarios.availability.attacker import \
    attacker_baremetal


class ExecuteShellTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_subprocess = mock.patch.object(attacker_baremetal,
                                                  'subprocess')
        self.mock_subprocess = self._mock_subprocess.start()

        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_subprocess.stop()

    def test__execute_shell_command_successful(self):
        self.mock_subprocess.check_output.return_value = (0, 'unittest')
        exitcode, _ = attacker_baremetal._execute_shell_command("env")
        self.assertEqual(exitcode, 0)

    @mock.patch.object(attacker_baremetal, 'LOG')
    def test__execute_shell_command_fail_cmd_exception(self, mock_log):
        self.mock_subprocess.check_output.side_effect = RuntimeError
        exitcode, _ = attacker_baremetal._execute_shell_command("env")
        self.assertEqual(exitcode, -1)
        mock_log.error.assert_called_once()


class AttackerBaremetalTestCase(unittest.TestCase):

    def setUp(self):
        self._mock_ssh = mock.patch.object(attacker_baremetal, 'ssh')
        self.mock_ssh = self._mock_ssh.start()
        self._mock_subprocess = mock.patch.object(attacker_baremetal,
                                                  'subprocess')
        self.mock_subprocess = self._mock_subprocess.start()
        self.addCleanup(self._stop_mocks)

        self.mock_ssh.SSH.from_node().execute.return_value = (
            0, "running", '')

        host = {
            "ipmi_ip": "10.20.0.5",
            "ipmi_user": "root",
            "ipmi_password": "123456",
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.attacker_cfg = {
            'fault_type': 'bear-metal-down',
            'host': 'node1',
        }

        self.ins = attacker_baremetal.BaremetalAttacker(self.attacker_cfg,
                                                        self.context)

    def _stop_mocks(self):
        self._mock_ssh.stop()
        self._mock_subprocess.stop()

    def test__attacker_baremetal_all_successful(self):
        self.ins.setup()
        self.ins.inject_fault()
        self.ins.recover()

    def test__attacker_baremetal_check_failure(self):
        self.mock_ssh.SSH.from_node().execute.return_value = (
            0, "error check", '')
        self.ins.setup()

    def test__attacker_baremetal_recover_successful(self):
        self.attacker_cfg["jump_host"] = 'node1'
        self.context["node1"]["password"] = "123456"
        ins = attacker_baremetal.BaremetalAttacker(self.attacker_cfg,
                                                   self.context)

        ins.setup()
        ins.recover()
