##############################################################################
# Copyright (c) 2018 Intel.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from yardstick.benchmark.contexts import base
from yardstick.benchmark.contexts import model


class FlagsTestCase(unittest.TestCase):

    def setUp(self):
        self.flags = base.Flags()

    def test___init__(self):
        self.assertFalse(self.flags.no_setup)
        self.assertFalse(self.flags.no_teardown)

    def test___init__with_flags(self):
        kwargs = {"no_setup": True}
        flags = base.Flags(no_setup=True)
        self.assertTrue(flags.no_setup)
        self.assertFalse(flags.no_teardown)

    def test_parse(self):
        ctx_flags = {
            'no_setup': True,
            'no_teardown': "False",
            }

        self.flags.parse(ctx_flags)

        self.assertTrue(self.flags.no_setup)
        self.assertEqual(self.flags.no_teardown, "False")

    def test_parse_forbidden_flags(self):
        ctx_flags = {
            'foo': 42,
        }
        self.flags.parse(ctx_flags)
        with self.assertRaises(AttributeError):
            self.flags.foo
