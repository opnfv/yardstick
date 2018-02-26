# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from yardstick.benchmark.contexts import base


class FlagsTestCase(unittest.TestCase):

    def setUp(self):
        self.flags = base.Flags()

    def test___init__(self):
        self.assertFalse(self.flags.no_setup)
        self.assertFalse(self.flags.no_teardown)

    def test___init__with_flags(self):
        flags = base.Flags(no_setup=True)
        self.assertTrue(flags.no_setup)
        self.assertFalse(flags.no_teardown)

    def test_parse(self):
        self.flags.parse(no_setup=True, no_teardown="False")

        self.assertTrue(self.flags.no_setup)
        self.assertEqual(self.flags.no_teardown, "False")

    def test_parse_forbidden_flags(self):
        self.flags.parse(foo=42)
        with self.assertRaises(AttributeError):
            _ = self.flags.foo
