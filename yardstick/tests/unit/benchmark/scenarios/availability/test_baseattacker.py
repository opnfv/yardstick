##############################################################################
# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import unittest

from yardstick.benchmark.scenarios.availability.attacker import baseattacker


class BaseAttackerTestCase(unittest.TestCase):

    def setUp(self):
        self.attacker_cfg = {
            'fault_type': 'test-attacker',
            'action_parameter': {'process_name': 'nova_api'},
            'rollback_parameter': {'process_name': 'nova_api'},
            'key': 'stop-service',
            'attack_key': 'stop-service',
            'host': 'node1',
        }
        self.base_attacker = baseattacker.BaseAttacker({}, {})

    def test__init__(self):
        self.assertEqual(self.base_attacker.data, {})
        self.assertFalse(self.base_attacker.mandatory)
        self.assertEqual(self.base_attacker.intermediate_variables, {})
        self.assertFalse(self.base_attacker.mandatory)

    def test_get_attacker_cls(self):
        with self.assertRaises(RuntimeError):
            baseattacker.BaseAttacker.get_attacker_cls(self.attacker_cfg)
