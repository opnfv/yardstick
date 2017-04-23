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
        self.template = heat.HeatTemplate('test')

    def test_add_tenant_network(self):
        self.template.add_network('some-network')

        self.assertEqual(self.template.resources['some-network']['type'], 'OS::Neutron::Net')

    def test_add_provider_network(self):
        self.template.add_network('some-network', 'physnet2', 'sriov')

        self.assertEqual(self.template.resources['some-network']['type'], 'OS::Neutron::ProviderNet')
        self.assertEqual(self.template.resources['some-network']['properties']['physical_network'], 'physnet2')

    def test_add_subnet(self):
        netattrs = {'cidr': '10.0.0.0/24', 'provider': None, 'external_network': 'ext_net'}
        self.template.add_subnet('some-subnet', "some-network", netattrs['cidr'])

        self.assertEqual(self.template.resources['some-subnet']['type'], 'OS::Neutron::Subnet')
        self.assertEqual(self.template.resources['some-subnet']['properties']['cidr'], '10.0.0.0/24')

    def test_add_router(self):
        self.template.add_router('some-router', 'ext-net', 'some-subnet')

        self.assertEqual(self.template.resources['some-router']['type'], 'OS::Neutron::Router')
        self.assertIn('some-subnet', self.template.resources['some-router']['depends_on'])

    def test_add_router_interface(self):
        self.template.add_router_interface('some-router-if', 'some-router', 'some-subnet')

        self.assertEqual(self.template.resources['some-router-if']['type'], 'OS::Neutron::RouterInterface')
        self.assertIn('some-subnet', self.template.resources['some-router-if']['depends_on'])

    def test_add_servergroup(self):
        self.template.add_servergroup('some-server-group', 'anti-affinity')

        self.assertEqual(self.template.resources['some-server-group']['type'], 'OS::Nova::ServerGroup')
        self.assertEqual(self.template.resources['some-server-group']['properties']['policies'], ['anti-affinity'])

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
