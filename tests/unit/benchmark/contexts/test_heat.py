#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.contexts.heat

from __future__ import absolute_import

import logging
import os
import unittest
import uuid
from collections import OrderedDict

import mock

from yardstick.benchmark.contexts import heat
from yardstick.benchmark.contexts import model


LOG = logging.getLogger(__name__)


class HeatContextTestCase(unittest.TestCase):

    def setUp(self):
        self.test_context = heat.HeatContext()
        self.mock_context = mock.Mock(spec=heat.HeatContext())

    def test_construct(self):

        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.stack)
        self.assertEqual(self.test_context.networks, OrderedDict())
        self.assertEqual(self.test_context.servers, [])
        self.assertEqual(self.test_context.placement_groups, [])
        self.assertEqual(self.test_context.server_groups, [])
        self.assertIsNone(self.test_context.keypair_name)
        self.assertIsNone(self.test_context.secgroup_name)
        self.assertEqual(self.test_context._server_map, {})
        self.assertIsNone(self.test_context._image)
        self.assertIsNone(self.test_context._flavor)
        self.assertIsNone(self.test_context._user)
        self.assertIsNone(self.test_context.template_file)
        self.assertIsNone(self.test_context.heat_parameters)
        self.assertIsNotNone(self.test_context.key_uuid)
        self.assertIsNotNone(self.test_context.key_filename)

    @mock.patch('yardstick.benchmark.contexts.heat.PlacementGroup')
    @mock.patch('yardstick.benchmark.contexts.heat.ServerGroup')
    @mock.patch('yardstick.benchmark.contexts.heat.Network')
    @mock.patch('yardstick.benchmark.contexts.heat.Server')
    def test_init(self, mock_server, mock_network, mock_sg, mock_pg):

        pgs = {'pgrp1': {'policy': 'availability'}}
        sgs = {'servergroup1': {'policy': 'affinity'}}
        networks = {'bar': {'cidr': '10.0.1.0/24'}}
        servers = {'baz': {'floating_ip': True, 'placement': 'pgrp1'}}
        attrs = {'name': 'foo',
                 'placement_groups': pgs,
                 'server_groups': sgs,
                 'networks': networks,
                 'servers': servers}

        self.test_context.init(attrs)

        self.assertEqual(self.test_context.name, "foo")
        self.assertEqual(self.test_context.keypair_name, "foo-key")
        self.assertEqual(self.test_context.secgroup_name, "foo-secgroup")

        mock_pg.assert_called_with('pgrp1', self.test_context,
                                   pgs['pgrp1']['policy'])
        mock_sg.assert_called_with('servergroup1', self.test_context,
                                   sgs['servergroup1']['policy'])
        self.assertTrue(len(self.test_context.placement_groups) == 1)
        self.assertTrue(len(self.test_context.server_groups) == 1)

        mock_network.assert_called_with(
            'bar', self.test_context, networks['bar'])
        self.assertTrue(len(self.test_context.networks) == 1)

        mock_server.assert_called_with('baz', self.test_context,
                                       servers['baz'])
        self.assertTrue(len(self.test_context.servers) == 1)

        if os.path.exists(self.test_context.key_filename):
            try:
                os.remove(self.test_context.key_filename)
                os.remove(self.test_context.key_filename + ".pub")
            except OSError:
                LOG.exception("key_filename: %s",
                              self.test_context.key_filename)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test__add_resources_to_template_no_servers(self, mock_template):

        self.test_context.keypair_name = "foo-key"
        self.test_context.secgroup_name = "foo-secgroup"
        self.test_context.key_uuid = "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b"
        netattrs = {'cidr': '10.0.0.0/24', 'provider': None, 'external_network': 'ext_net'}
        self.mock_context.name = 'bar'
        self.test_context.networks = OrderedDict(
            {"fool-network": model.Network("fool-network", self.mock_context,
                                           netattrs)})

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with(
            "foo-key",
            "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b")
        mock_template.add_security_group.assert_called_with("foo-secgroup")
#        mock_template.add_network.assert_called_with("bar-fool-network", 'physnet1', None)
        mock_template.add_router.assert_called_with("bar-fool-network-router", netattrs["external_network"], "bar-fool-network-subnet")
        mock_template.add_router_interface.assert_called_with("bar-fool-network-router-if0", "bar-fool-network-router", "bar-fool-network-subnet")

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    @mock.patch('yardstick.benchmark.contexts.heat.get_neutron_client')
    def test_deploy(self, mock_neutron, mock_template):

        self.test_context.name = 'foo'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.heat_timeout = 5
        self.test_context.deploy()

        mock_template.assert_called_with(self.test_context.name,
                                         self.test_context.template_file,
                                         self.test_context.heat_parameters)
        self.assertIsNotNone(self.test_context.stack)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_undeploy(self, mock_template):

        self.test_context.stack = mock_template
        self.test_context.undeploy()

        self.assertTrue(mock_template.delete.called)

    def test__get_server(self):

        self.mock_context.name = 'bar'
        self.mock_context.stack.outputs = {'public_ip': '127.0.0.1',
                                           'private_ip': '10.0.0.1'}
        self.mock_context.key_uuid = uuid.uuid4()

        attr_name = {'name': 'foo.bar',
                     'public_ip_attr': 'public_ip',
                     'private_ip_attr': 'private_ip'}
        result = heat.HeatContext._get_server(self.mock_context, attr_name)

        self.assertEqual(result['ip'], '127.0.0.1')
        self.assertEqual(result['private_ip'], '10.0.0.1')
