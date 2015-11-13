#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.attacker.baseattacker

import mock
import unittest

from yardstick.benchmark.scenarios.availability.attacker import baseattacker


class AttackerMgrTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.availability.attacker.baseattacker.BaseAttacker')
    def test__AttackerMgr_all_successful(self, mock_base_attacker):
        config = {
            "service_name": "nova-api",
            "fault_type": "stop-service"
        }

        configs = []
        configs.append(config)

        instance = baseattacker.AttackerMgr()
        instance.setup(configs)

        instance_count = len(instance.attacker_list)

        self.assertEqual(instance_count, 1)

        instance.do_attack()
        instance.stop_attack()

    @mock.patch('yardstick.benchmark.scenarios.availability.attacker.baseattacker.BaseAttacker')
    def test__AttackerMgr_setup_servicename_error(self, mock_base_attacker):
        config = {
            "service_name": "error-service-name",
            "fault_type": "stop-service"
        }

        configs = []
        configs.append(config)

        instance = baseattacker.AttackerMgr()
        instance.setup(configs)

        instance_count = len(instance.attacker_list)

        self.assertEqual(instance_count, 0)

    @mock.patch('yardstick.benchmark.scenarios.availability.attacker.baseattacker.BaseAttacker')
    def test__AttackerMgr_setup_fault_type_error(self, mock_base_attacker):
        config = {
            "service_name": "nova-api",
            "fault_type": "error-fault-type"
        }

        configs = []
        configs.append(config)

        instance = baseattacker.AttackerMgr()
        instance.setup(configs)

        instance_count = len(instance.attacker_list)

        self.assertEqual(instance_count, 0)


class AttackerBaseTestCase(unittest.TestCase):

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

    def test__attacker_get_attacker_successful(self):

        self.config["fault_type"] = "stop-service"
        instance = baseattacker.BaseAttacker.get_attacker(self.config)
        self.assertIsNotNone(instance)

    def test__attacker_get_attacker_check_failuer(self):
        instance = None
        try:
            self.config["fault_type"] = "error-attacker-type"
            instance = baseattacker.BaseAttacker.get_attacker(self.config)
        except Exception:
            pass
        self.assertIsNone(instance)
