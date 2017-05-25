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
# yardstick.benchmark.scenarios.availability.attacker.attacker_process

from __future__ import absolute_import
import mock
import unittest

from yardstick.benchmark.scenarios.availability.attacker import baseattacker


@mock.patch(
    'yardstick.benchmark.scenarios.availability.attacker.attacker_process.ssh')
class AttackerServiceTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        self.context = {"node1": host}
        self.attacker_cfg = {
            'fault_type': 'kill-process',
            'process_name': 'nova-api',
            'host': 'node1',
        }

    def test__attacker_service_all_successful(self, mock_ssh):

        cls = baseattacker.BaseAttacker.get_attacker_cls(self.attacker_cfg)
        ins = cls(self.attacker_cfg, self.context)

        mock_ssh.SSH.from_node().execute.return_value = (0, "10", '')
        ins.setup()
        ins.inject_fault()
        ins.recover()

    def test__attacker_service_check_failuer(self, mock_ssh):

        cls = baseattacker.BaseAttacker.get_attacker_cls(self.attacker_cfg)
        ins = cls(self.attacker_cfg, self.context)

        mock_ssh.SSH.from_node().execute.return_value = (0, None, '')
        ins.setup()
