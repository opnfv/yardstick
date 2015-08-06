#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.context.model

import mock
import unittest

from yardstick.benchmark.context import model


class ObjectTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()

    def test_construct(self):

        test_object = model.Object('foo', self.mock_context)

        self.assertEqual(test_object.name, 'foo')
        self.assertEqual(test_object._context, self.mock_context)
        self.assertIsNone(test_object.stack_name)
        self.assertIsNone(test_object.stack_id)

    def test_dn(self):

        self.mock_context.name = 'bar'
        test_object = model.Object('foo', self.mock_context)

        self.assertEqual('foo.bar', test_object.dn)


class PlacementGroupTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'

    def tearDown(self):
        model.PlacementGroup.map = {}

    def test_sucessful_construct(self):

        test_pg = model.PlacementGroup('foo', self.mock_context, 'affinity')

        self.assertEqual(test_pg.name, 'foo')
        self.assertEqual(test_pg.members, set())
        self.assertEqual(test_pg.stack_name, 'bar-foo')
        self.assertEqual(test_pg.policy, 'affinity')

        test_map = {'foo': test_pg}
        self.assertEqual(model.PlacementGroup.map, test_map)

    def test_wrong_policy_in_construct(self):

        self.assertRaises(ValueError, model.PlacementGroup, 'foo',
                          self.mock_context, 'baz')

    def test_add_member(self):

        test_pg = model.PlacementGroup('foo', self.mock_context, 'affinity')
        test_pg.add_member('foo')

        self.assertEqual(test_pg.members, set(['foo']))

    def test_get_name_successful(self):

        model.PlacementGroup.map = {'foo': True}
        self.assertTrue(model.PlacementGroup.get('foo'))

    def test_get_name_unsuccessful(self):

        self.assertIsNone(model.PlacementGroup.get('foo'))


class RouterTestCase(unittest.TestCase):

    def test_construct(self):

        mock_context = mock.Mock()
        mock_context.name = 'baz'
        test_router = model.Router('foo', 'bar', mock_context, 'qux')

        self.assertEqual(test_router.stack_name, 'baz-bar-foo')
        self.assertEqual(test_router.stack_if_name, 'baz-bar-foo-if0')
        self.assertEqual(test_router.external_gateway_info, 'qux')


class NetworkTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'

    def tearDown(self):
        model.Network.list = []

    def test_construct_no_external_network(self):

        attrs = {'cidr': '10.0.0.0/24'}
        test_network = model.Network('foo', self.mock_context, attrs)

        self.assertEqual(test_network.stack_name, 'bar-foo')
        self.assertEqual(test_network.subnet_stack_name, 'bar-foo-subnet')
        self.assertEqual(test_network.subnet_cidr, attrs['cidr'])
        self.assertIsNone(test_network.router)
        self.assertIn(test_network, model.Network.list)

    def test_construct_has_external_network(self):

        attrs = {'external_network': 'ext_net'}
        test_network = model.Network('foo', self.mock_context, attrs)
        exp_router = model.Router('router', 'foo', self.mock_context, 'ext_net')

        self.assertEqual(test_network.router.stack_name, exp_router.stack_name)
        self.assertEqual(test_network.router.stack_if_name,
                         exp_router.stack_if_name)
        self.assertEqual(test_network.router.external_gateway_info,
                         exp_router.external_gateway_info)

    def test_has_route_to(self):

        attrs = {'external_network': 'ext_net'}
        test_network = model.Network('foo', self.mock_context, attrs)

        self.assertTrue(test_network.has_route_to('ext_net'))

    def test_has_no_route_to(self):

        attrs = {}
        test_network = model.Network('foo', self.mock_context, attrs)

        self.assertFalse(test_network.has_route_to('ext_net'))

    @mock.patch('yardstick.benchmark.context.model.Network.has_route_to')
    def test_find_by_route_to(self, mock_has_route_to):

        mock_network = mock.Mock()
        model.Network.list = [mock_network]
        mock_has_route_to.return_value = True

        self.assertIs(mock_network, model.Network.find_by_route_to('foo'))

    def test_find_external_network(self):

        mock_network = mock.Mock()
        mock_network.router = mock.Mock()
        mock_network.router.external_gateway_info = 'ext_net'
        model.Network.list = [mock_network]

        self.assertEqual(model.Network.find_external_network(), 'ext_net')


class ServerTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_context = mock.Mock()
        self.mock_context.name = 'bar'
        self.mock_context.keypair_name = 'some-keys'
        self.mock_context.secgroup_name = 'some-secgroup'

    def test_construct_defaults(self):

        attrs = None
        test_server = model.Server('foo', self.mock_context, attrs)

        self.assertEqual(test_server.stack_name, 'foo.bar')
        self.assertEqual(test_server.keypair_name, 'some-keys')
        self.assertEqual(test_server.secgroup_name, 'some-secgroup')
        self.assertEqual(test_server.placement_groups, [])
        self.assertEqual(test_server.instances, 1)
        self.assertIsNone(test_server.floating_ip)
        self.assertIsNone(test_server._image)
        self.assertIsNone(test_server._flavor)
        self.assertIn(test_server, model.Server.list)

    @mock.patch('yardstick.benchmark.context.model.PlacementGroup')
    def test_construct_get_wrong_placement_group(self, mock_pg):

        attrs = {'placement': 'baz'}
        mock_pg.get.return_value = None

        self.assertRaises(ValueError, model.Server, 'foo',
                          self.mock_context, attrs)

    @mock.patch('yardstick.benchmark.context.model.HeatTemplate')
    def test__add_instance(self, mock_template):

        attrs = {'image': 'some-image', 'flavor': 'some-flavor'}
        test_server = model.Server('foo', self.mock_context, attrs)

        mock_network = mock.Mock()
        mock_network.name = 'some-network'
        mock_network.stack_name = 'some-network-stack'
        mock_network.subnet_stack_name = 'some-network-stack-subnet'

        test_server._add_instance(mock_template, 'some-server',
                                  [mock_network], 'hints')

        mock_template.add_port.assert_called_with(
            'some-server-some-network-port',
            mock_network.stack_name,
            mock_network.subnet_stack_name,
            sec_group_id=self.mock_context.secgroup_name)

        mock_template.add_server.assert_called_with(
            'some-server', 'some-image', 'some-flavor',
            ports=['some-server-some-network-port'],
            key_name=self.mock_context.keypair_name,
            scheduler_hints='hints')


class ContextTestCase(unittest.TestCase):

    def setUp(self):
        self.test_context = model.Context()
        self.mock_context = mock.Mock()

    def tearDown(self):
        model.Context.list = []

    def test_construct(self):

        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.stack)
        self.assertEqual(self.test_context.networks, [])
        self.assertEqual(self.test_context.servers, [])
        self.assertEqual(self.test_context.placement_groups, [])
        self.assertIsNone(self.test_context.keypair_name)
        self.assertIsNone(self.test_context.secgroup_name)
        self.assertEqual(self.test_context._server_map, {})
        self.assertIsNone(self.test_context._image)
        self.assertIsNone(self.test_context._flavor)
        self.assertIsNone(self.test_context._user)
        self.assertIsNone(self.test_context.template_file)
        self.assertIsNone(self.test_context.heat_parameters)
        self.assertIn(self.test_context, model.Context.list)

    @mock.patch('yardstick.benchmark.context.model.PlacementGroup')
    @mock.patch('yardstick.benchmark.context.model.Network')
    @mock.patch('yardstick.benchmark.context.model.Server')
    def test_init(self, mock_server, mock_network, mock_pg):

        pgs = {'pgrp1': {'policy': 'availability'}}
        networks = {'bar': {'cidr': '10.0.1.0/24'}}
        servers = {'baz': {'floating_ip': True, 'placement': 'pgrp1'}}
        attrs = {'name': 'foo',
                 'placement_groups': pgs,
                 'networks': networks,
                 'servers': servers}

        self.test_context.init(attrs)

        self.assertEqual(self.test_context.keypair_name, "foo-key")
        self.assertEqual(self.test_context.secgroup_name, "foo-secgroup")

        mock_pg.assert_called_with('pgrp1', self.test_context,
                                   pgs['pgrp1']['policy'])
        self.assertTrue(len(self.test_context.placement_groups) == 1)

        mock_network.assert_called_with(
            'bar', self.test_context, networks['bar'])
        self.assertTrue(len(self.test_context.networks) == 1)

        mock_server.assert_called_with('baz', self.test_context, servers['baz'])
        self.assertTrue(len(self.test_context.servers) == 1)

    @mock.patch('yardstick.benchmark.context.model.HeatTemplate')
    def test__add_resources_to_template_no_servers(self, mock_template):

        self.test_context.keypair_name = "foo-key"
        self.test_context.secgroup_name = "foo-secgroup"

        self.test_context._add_resources_to_template(mock_template)
        mock_template.add_keypair.assert_called_with("foo-key")
        mock_template.add_security_group.assert_called_with("foo-secgroup")

    @mock.patch('yardstick.benchmark.context.model.HeatTemplate')
    def test_deploy(self, mock_template):

        self.test_context.name = 'foo'
        self.test_context.template_file = '/bar/baz/some-heat-file'
        self.test_context.heat_parameters = {'image': 'cirros'}
        self.test_context.deploy()

        mock_template.assert_called_with(self.test_context.name,
                                         self.test_context.template_file,
                                         self.test_context.heat_parameters)
        self.assertIsNotNone(self.test_context.stack)

    @mock.patch('yardstick.benchmark.context.model.HeatTemplate')
    def test_undeploy(self, mock_template):

        self.test_context.stack = mock_template
        self.test_context.undeploy()

        self.assertTrue(mock_template.delete.called)

    def test_get_server_by_name(self):

        self.mock_context._server_map = {'foo.bar': True}
        model.Context.list = [self.mock_context]

        self.assertTrue(model.Context.get_server_by_name('foo.bar'))

    def test_get_server_by_wrong_name(self):

        self.assertRaises(ValueError, model.Context.get_server_by_name, 'foo')

    def test_get_context_by_name(self):

        self.mock_context.name = 'foo'
        model.Context.list = [self.mock_context]

        self.assertIs(model.Context.get_context_by_name('foo'),
                      self.mock_context)

    def test_get_unknown_context_by_name(self):

        model.Context.list = []
        self.assertIsNone(model.Context.get_context_by_name('foo'))

    @mock.patch('yardstick.benchmark.context.model.Server')
    def test_get_server(self, mock_server):

        self.mock_context.name = 'bar'
        self.mock_context.stack.outputs = {'public_ip': '127.0.0.1',
                                           'private_ip': '10.0.0.1'}
        model.Context.list = [self.mock_context]
        attr_name = {'name': 'foo.bar',
                     'public_ip_attr': 'public_ip',
                     'private_ip_attr': 'private_ip'}
        result = model.Context.get_server(attr_name)

        self.assertEqual(result.public_ip, '127.0.0.1')
        self.assertEqual(result.private_ip, '10.0.0.1')
