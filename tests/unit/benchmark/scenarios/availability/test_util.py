#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Juan Qiu and others
# juan_qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.availability.director

from __future__ import absolute_import
import mock
import unittest
from yardstick.benchmark.scenarios.availability import util

class UtilTestCase(unittest.TestCase):

    def setUp(self):
        self.param_config = {'serviceName':'$serviceName','value': 1}
        self.intermediate_variables = {'$serviceName':'nova-api'}

    def test_util_build_command_shell(self):
        result = util.build_shell_command(self.param_config, True,
                                          self.intermediate_variables)
        expected_vaule = "/bin/bash -s nova-api 1"
        self.assertEqual(expected_vaule, result)
