#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.dummy.dummy

from __future__ import absolute_import
import unittest

from yardstick.benchmark.scenarios.dummy import dummy


class DummyTestCase(unittest.TestCase):

    def setUp(self):
        self.test_context = dummy.Dummy(None, None)

        self.assertIsNone(self.test_context.scenario_cfg)
        self.assertIsNone(self.test_context.context_cfg)
        self.assertEqual(self.test_context.setup_done, False)

    def test_run(self):
        result = {}
        self.test_context.run(result)

        self.assertEqual(result["hello"], "yardstick")
        self.assertEqual(self.test_context.setup_done, True)
