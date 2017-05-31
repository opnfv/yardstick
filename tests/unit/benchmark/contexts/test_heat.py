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
        self.assertEqual(self.test_context.networks, [])
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
        self.test_context.networks = [model.Network("fool-network", self.mock_context, netattrs)]

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with(
            "foo-key",
            "2f2e4997-0a8e-4eb7-9fa4-f3f8fbbc393b")
        mock_template.add_security_group.assert_called_with("foo-secgroup")
#        mock_template.add_network.assert_called_with("bar-fool-network", 'physnet1', None)
        mock_template.add_router.assert_called_with("bar-fool-network-router", netattrs["external_network"], "bar-fool-network-subnet")
        mock_template.add_router_interface.assert_called_with("bar-fool-network-router-if0", "bar-fool-network-router", "bar-fool-network-subnet")

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_image_flavor_user(self, mock_template):
        self.test_context._image = 'foo'
        self.assertIsNotNone(self.test_context.image)
        self.test_context._flavor = 'foo'
        self.assertIsNotNone(self.test_context.flavor)
        self.test_context._user = 'foo'
        self.assertIsNotNone(self.test_context.user)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_deploy(self, mock_template):

        self.test_context.name = 'foo'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.deploy()

        mock_template.assert_called_with(self.test_context.name,
                                         self.test_context.template_file,
                                         self.test_context.heat_parameters)
        self.assertIsNotNone(self.test_context.stack)

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    def test_deploy(self, mock_template):

        self.test_context.name = 'foo'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
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

    @mock.patch('yardstick.benchmark.contexts.heat.HeatTemplate')
    @mock.patch('yardstick.benchmark.contexts.heat.os')
    def test_undeploy_key_filename(self, mock_template, mock_os):

        self.test_context.stack = mock_template
        mock_os.path = mock.MagicMock()
        mock_os.path.exists = mock.Mock(return_value=True)
        self.assertEqual(None, self.test_context.undeploy())

    def test__get_context_from_server_with_dic_attr_name(self):
        self.mock_context.name = 'bar'
        self.mock_context.stack.outputs = {'public_ip': '127.0.0.1',
                                           'private_ip': '10.0.0.1'}
        self.mock_context.key_uuid = uuid.uuid4()

        attr_name = {'name': 'foo.bar',
                     'public_ip_attr': 'public_ip',
                     'private_ip_attr': 'private_ip'}

        attr_name = {'name': 'foo.bar'}
        result = self.test_context._get_context_from_server(attr_name)

        self.assertEqual(result, None)

    def test__get_context_from_server_not_found(self):

        attr_name = 'bar.foo1'
        self.test_context.name = "foo"
        result = self.test_context._get_context_from_server(attr_name)

        self.assertEqual(result, None)

    def test__get_context_from_server_found(self):

        attr_name = 'node1.foo'
        self.test_context.name = "foo"
        result = self.test_context._get_context_from_server(attr_name)

        self.assertEqual(result, {})

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

    def test__get_server_not_found(self):

        self.mock_context.name = 'bar1'
        self.mock_context.stack.outputs = {'public_ip': '127.0.0.1',
                                           'private_ip': '10.0.0.1'}
        self.mock_context.key_uuid = uuid.uuid4()

        attr_name = {'name': 'foo.bar',
                     'public_ip_attr': 'public_ip',
                     'private_ip_attr': 'private_ip'}
        result = heat.HeatContext._get_server(self.mock_context, attr_name)

        self.assertEqual(result, None)

    def test__get_server_not_dict(self):

        self.mock_context.name = 'bar1'
        self.mock_context.stack.outputs = {'public_ip': '127.0.0.1',
                                           'private_ip': '10.0.0.1'}
        self.mock_context.key_uuid = uuid.uuid4()

        attr_name = 'foo.bar'
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)
        self.test_context._server_map = [1, None, 3]
        attr_name = 1
        result = self.test_context._get_server(attr_name)
        self.assertEqual(result, None)
