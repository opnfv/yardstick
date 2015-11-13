#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.attacker.attacker_service

import mock
import unittest

from yardstick.benchmark.scenarios.availability.attacker import attacker_service

@mock.patch('yardstick.benchmark.scenarios.availability.attacker.attacker_service.ssh')
class AttackerServiceTestCase(unittest.TestCase):

    def setUp(self):
        host = {
            "ip": "10.20.0.5",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        fault_cfg = {
            "check_script": "scripts/check_service.bash",
            "inject_script": "scripts/stop_service.bash",
            "recovery_script": "scripts/start_service.bash"
        }
        self.config = {
            "host": host,
            "service_name": "nova-api",
            "fault_cfg": fault_cfg
        }


    def test__attacker_service_all_successful(self, mock_ssh):

        instance = attacker_service.ServiceAttacker(self.config)

        mock_ssh.SSH().execute.return_value = (0, "running", '')
        instance.run()

    def test__attacker_service_check_failuer(self, mock_ssh):

        instance = attacker_service.ServiceAttacker(self.config)

        mock_ssh.SSH().execute.return_value = (0, "error check", '')
        instance.run()

