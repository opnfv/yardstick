#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.dummy

from __future__ import absolute_import
import unittest

from yardstick.benchmark.contexts import dummy


class DummyContextTestCase(unittest.TestCase):

    def setUp(self):
        self.test_context = dummy.DummyContext()

    def test__get_server(self):
        self.test_context.init(None)
        self.test_context.deploy()

        result = self.test_context._get_server(None)
        self.assertEqual(result, None)

        self.test_context.undeploy()
