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
import mock

from yardstick.orchestrator import heat


class HeatContextTestCase(unittest.TestCase):

    def test_get_short_key_uuid(self):
        u = uuid.uuid4()
        k = heat.get_short_key_uuid(u)
        self.assertEqual(heat.HEAT_KEY_UUID_LENGTH, len(k))
        self.assertIn(k, str(u))

class HeatTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'

    def test_add_servergroup(self):
        
        template = heat.HeatTemplate('test')
        template.add_servergroup('some-server-group', 'anti-affinity')

        self.assertEqual(template.resources['some-server-group']['type'], 'OS::Nova::ServerGroup')
        self.assertEqual(template.resources['some-server-group']['properties']['policies'], ['anti-affinity'])

class HeatStackTestCase(unittest.TestCase):

    def test_delete_calls__delete_multiple_times(self):
        stack = heat.HeatStack('test')
        stack.uuid = 1
        with mock.patch.object(stack, "_delete") as delete_mock:
            stack.delete()
        # call once and then call again if uuid is not none
        self.assertGreater(delete_mock.call_count, 1)

    def test_delete_all_calls_delete(self):
        stack = heat.HeatStack('test')
        stack.uuid = 1
        with mock.patch.object(stack, "delete") as delete_mock:
            stack.delete_all()
        self.assertGreater(delete_mock.call_count, 0)
