##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import unittest

from yardstick.benchmark.contexts import dummy


class DummyContextTestCase(unittest.TestCase):

    def setUp(self):
        self.attrs = {
            'name': 'foo',
            'task_id': '1234567890',
        }
        self.test_context = dummy.DummyContext()
        self.addCleanup(self.test_context._delete_context)

    def test___init__(self):
        self.assertFalse(self.test_context._flags.no_setup)
        self.assertFalse(self.test_context._flags.no_teardown)
        self.assertIsNone(self.test_context._name)
        self.assertIsNone(self.test_context._task_id)

    def test_init(self):
        self.test_context.init(self.attrs)
        self.assertEqual(self.test_context._name, 'foo')
        self.assertEqual(self.test_context._task_id, '1234567890')
        self.assertFalse(self.test_context._flags.no_setup)
        self.assertFalse(self.test_context._flags.no_teardown)

        self.assertEqual(self.test_context.name, 'foo-12345678')
        self.assertEqual(self.test_context.assigned_name, 'foo')

    def test_init_flags_no_setup(self):
        self.attrs['flags'] = {'no_setup': True, 'no_teardown': False}

        self.test_context.init(self.attrs)

        self.assertEqual(self.test_context._name, 'foo')
        self.assertEqual(self.test_context._task_id, '1234567890')
        self.assertTrue(self.test_context._flags.no_setup)
        self.assertFalse(self.test_context._flags.no_teardown)

        self.assertEqual(self.test_context.name, 'foo')
        self.assertEqual(self.test_context.assigned_name, 'foo')

    def test_init_flags_no_teardown(self):
        self.attrs['flags'] = {'no_setup': False, 'no_teardown': True}

        self.test_context.init(self.attrs)

        self.assertFalse(self.test_context._flags.no_setup)
        self.assertTrue(self.test_context._flags.no_teardown)

        self.assertEqual(self.test_context.name, 'foo')
        self.assertEqual(self.test_context.assigned_name, 'foo')

    def test__get_server(self):
        self.test_context.init(self.attrs)
        self.test_context.deploy()

        result = self.test_context._get_server(None)
        self.assertEqual(result, None)

        self.test_context.undeploy()
