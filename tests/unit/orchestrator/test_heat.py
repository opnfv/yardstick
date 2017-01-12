#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.orchestrator.heat

import unittest
import uuid

from yardstick.orchestrator import heat


class HeatContextTestCase(unittest.TestCase):

    def test_get_short_key_uuid(self):
        u = uuid.uuid4()
        k = heat.get_short_key_uuid(u)
        self.assertEqual(heat.HEAT_KEY_UUID_LENGTH, len(k))
        self.assertIn(k, str(u))
